import os
import sys
import traceback
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFileSystemModel, QTreeView, QLabel, QPushButton, 
                             QScrollArea, QSplitter, QToolBar, QSizePolicy, QLineEdit,
                             QComboBox, QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStackedWidget, QMessageBox, QStyledItemDelegate)
from PyQt5.QtGui import QPixmap, QImage, QPalette, QTransform, QMouseEvent, QPainter, QColor, QFont, QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QDir, QSize, QRect, QTimer, QThread, pyqtSignal

from mxx_processor import ReIDDataset

class AttributeDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.img_obj = None

    def createEditor(self, parent, option, index):
        if not self.img_obj:
            return None
            
        model = index.model()
        key_item = model.item(index.row(), 0)
        if not key_item:
            return None
        key = key_item.text()
        
        key_bool_list = []
        if hasattr(self.img_obj, 'get_key_bool_list'):
            key_bool_list = self.img_obj.get_key_bool_list()
        
        key_str_list = []
        if hasattr(self.img_obj, 'get_key_str_list'):
            key_str_list = self.img_obj.get_key_str_list()

        if key in key_bool_list:
            editor = QComboBox(parent)
            editor.addItems(["yes", "no"])
            return editor
        elif key in key_str_list:
            return QLineEdit(parent)
        else:
            return None

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if isinstance(editor, QComboBox):
            editor.setCurrentText(str(value))
        elif isinstance(editor, QLineEdit):
            editor.setText(str(value))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QComboBox):
            new_value = editor.currentText()
        elif isinstance(editor, QLineEdit):
            new_value = editor.text()
        else:
            super().setModelData(editor, model, index)
            return

        key_item = model.item(index.row(), 0)
        key = key_item.text()
        old_value = model.data(index, Qt.EditRole)

        if str(old_value) == new_value:
            return

        reply = QMessageBox.question(self.parent(), '确认修改', 
                                     f"确定要将属性 '{key}' 的值从 '{old_value}' 修改为 '{new_value}' 吗?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                self.img_obj[key] = new_value
                if hasattr(self.img_obj, 'save'):
                    self.img_obj.save()
                
                model.setData(index, new_value, Qt.EditRole)
                
                window = self.parent()
                if isinstance(window, QMainWindow):
                    window.statusBar().showMessage(f"属性 '{key}' 已更新为 '{new_value}'", 3000)
            except Exception as e:
                QMessageBox.critical(self.parent(), "错误", f"修改属性失败: {str(e)}")

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class ImageLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)  # 启用鼠标追踪
        self.original_pixmap = None
        self.scale_factor = 1.0
        self.image_name = ""  # 添加图片名属性
        
    def setImageName(self, name):
        """设置图片名"""
        self.image_name = name
        self.update()  # 触发重绘
        
    def paintEvent(self, event):
        """重写绘制事件，添加图片名标签"""
        super().paintEvent(event)
        if self.image_name:
            painter = QPainter(self)
            painter.setPen(Qt.white)  # 设置文字颜色为白色
            painter.setFont(QFont("Arial", 10))  # 设置字体
            
            # 创建半透明背景
            text_rect = QRect(0, 0, self.width(), 30)
            painter.fillRect(text_rect, QColor(0, 0, 0, 128))  # 半透明黑色背景
            
            # 绘制文字
            painter.drawText(text_rect, Qt.AlignCenter, self.image_name)
        
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton and self.original_pixmap:
            # 获取点击位置相对于图片的坐标
            pos = event.pos()
            
            # 获取图片在标签中的实际显示区域
            pixmap_rect = self.rect()
            pixmap_size = self.pixmap().size()
            
            # 计算图片在标签中的实际位置（居中显示）
            x_offset = (pixmap_rect.width() - pixmap_size.width()) // 2
            y_offset = (pixmap_rect.height() - pixmap_size.height()) // 2
            
            # 计算相对于图片的坐标
            x = pos.x() - x_offset
            y = pos.y() - y_offset
            
            # 检查点击是否在图片范围内
            if 0 <= x < pixmap_size.width() and 0 <= y < pixmap_size.height():
                # 计算原始图片中的坐标
                original_x = int(x / self.scale_factor)
                original_y = int(y / self.scale_factor)
                
                # 确保坐标在原始图片范围内
                if 0 <= original_x < self.original_pixmap.width() and 0 <= original_y < self.original_pixmap.height():
                    # 获取父窗口的状态栏
                    main_window = self.window()
                    if main_window:
                        # 获取点击位置的颜色
                        color = self.original_pixmap.toImage().pixelColor(original_x, original_y)
                        main_window.statusBar().showMessage(
                            f"点击位置: ({original_x}, {original_y}), 颜色: RGB({color.red()}, {color.green()}, {color.blue()})")


class ImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ReID Viewer')
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置默认路径
        self.default_path = '/Users/curarpikt/Documents/datasets/ReID/Market-1501-v15.09.15'
        
        # 初始化所有变量
        self.current_folder = None
        self.current_image_path = None
        self.image_labels = []  # 存储所有图像标签
        self.image_files = []
        self.current_image_index = -1
        self.scale_factor = 1.0
        self._dataset = None
        self._person_selected = None
        self._img_tgt = None
        self._img_ref_list = []
        self._img_previewed_right = None
        
        # 初始化数据集
        try:
            self._dataset = ReIDDataset(
                path_cfg='./humandataset_market_train.yaml',
                img_size_pad=(512, 512),
                stage=1,             
            )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"初始化数据集失败: {str(e)}")
            print(f"数据集初始化错误: {traceback.format_exc()}")
        
        # 初始化UI
        self.initUI()
        
        # 设置定时器用于处理事件循环
        self.timer = QTimer()
        self.timer.timeout.connect(self.process_events)
        self.timer.start(100)  # 每100ms处理一次事件

    def process_events(self):
        """处理Qt事件循环，防止界面卡死"""
        QApplication.processEvents()

    def _get_img_label(self):
        label = ImageLabel()
        label.setAlignment(Qt.AlignCenter)
        label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        label.setScaledContents(False)
        return label

    def _create_direction_table(self):
        table = QTableWidget()
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["文件名"])
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        return table

    def _populate_direction_table(self, table, img_list):
        table.setRowCount(0)
        if not img_list:
            return
        table.setRowCount(len(img_list))
        for i, img_item in enumerate(img_list):
            try:
                name = img_item.get_name_img()
                table.setItem(i, 0, QTableWidgetItem(name))
            except Exception as e:
                print(f"Error getting img name: {e}")
                table.setItem(i, 0, QTableWidgetItem("Error"))

    def _populate_attribute_view(self, model, img_obj):
        """Helper function to populate a tree model with image attributes."""
        model.clear()
        model.setHorizontalHeaderLabels(["属性", "值"])
        if not img_obj or not hasattr(img_obj, 'keys'):
            return
        
        root_item = model.invisibleRootItem()
        # Ensure it's a 2-column model for attributes
        if model.columnCount() < 2:
            model.setColumnCount(2)
            
        key_bool_list = []
        if hasattr(img_obj, 'get_key_bool_list'):
            key_bool_list = img_obj.get_key_bool_list()
        
        key_str_list = []
        if hasattr(img_obj, 'get_key_str_list'):
            key_str_list = img_obj.get_key_str_list()
        
        editable_keys = key_bool_list + key_str_list

        keys = list(img_obj.keys())
        for key in keys:
            try:
                value_str = str(img_obj[key])
            except Exception:
                value_str = "Error reading value"
            key_item = QStandardItem(str(key))
            key_item.setEditable(False)
            value_item = QStandardItem(value_str)
            if key in editable_keys:
                value_item.setEditable(True)
            else:
                value_item.setEditable(False)
            root_item.appendRow([key_item, value_item])

    def initUI(self):
        # 主窗口部件和布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 使用QSplitter实现可调整大小的左右分割
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_splitter = QSplitter(Qt.Vertical)

        # 左侧上部: 列表
        top_left_widget = QWidget()
        top_left_layout = QVBoxLayout(top_left_widget)
        top_left_layout.setContentsMargins(0,0,0,0)

        self.left_btn_bar = QHBoxLayout()
        self.btn_back = QPushButton("返回")
        self.btn_back.setVisible(False)  # 初始隐藏返回按钮
        self.btn_back.clicked.connect(self.on_back_clicked)
        self.left_btn_bar.addWidget(self.btn_back)
        self.left_btn_bar.addStretch()
        top_left_layout.addLayout(self.left_btn_bar)
        
        self.left_stack = QStackedWidget()
        
        # 第一级：行人ID列表
        self.tree_view = QTreeView()
        self.person_model = QStandardItemModel()
        self.person_model.setHorizontalHeaderLabels(["行人ID"])
        
        # 安全地获取行人ID列表
        try:
            if self._dataset:
                keys_id_person = self._dataset.get_person_keys()
                # 将ID转换为整数进行排序
                keys_sorted = sorted(keys_id_person, key=lambda x: int(x))
                for pid in keys_sorted:
                    item = QStandardItem(str(pid))
                    self.person_model.appendRow(item)
        except Exception as e:
            QMessageBox.warning(self, "警告", f"加载行人ID列表失败: {str(e)}")
            print(f"加载行人ID列表错误: {traceback.format_exc()}")
        
        self.tree_view.setModel(self.person_model)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setAnimated(False)
        self.tree_view.setIndentation(20)
        self.tree_view.setSortingEnabled(False)
        self.tree_view.clicked.connect(self.on_tree_view_person_clicked)
        self.left_stack.addWidget(self.tree_view)
        
        # 第二级：具体ID下的图片列表
        self.detail_view = QTreeView()
        self.detail_model = QStandardItemModel()
        self.detail_model.setHorizontalHeaderLabels(["图片"])
        self.detail_view.setModel(self.detail_model)
        self.detail_view.setHeaderHidden(False)
        self.detail_view.setAnimated(False)
        self.detail_view.setIndentation(20)
        self.detail_view.setSortingEnabled(False)
        self.detail_view.clicked.connect(self.on_detail_view_clicked)
        self.left_stack.addWidget(self.detail_view)
        
        top_left_layout.addWidget(self.left_stack)
        left_splitter.addWidget(top_left_widget)
        
        # 左侧下部: 主图属性
        self.left_attr_tree_view = QTreeView()
        self.left_attr_tree_model = QStandardItemModel()
        self.left_attr_tree_model.setHorizontalHeaderLabels(["属性", "值"])
        self.left_attr_tree_view.setModel(self.left_attr_tree_model)
        self.left_attr_delegate = AttributeDelegate(self)
        self.left_attr_tree_view.setItemDelegateForColumn(1, self.left_attr_delegate)
        left_splitter.addWidget(self.left_attr_tree_view)
        left_splitter.setSizes([600, 200])

        left_layout.addWidget(left_splitter)
        splitter.addWidget(left_widget)
        
        # 中间图片显示区域
        middle_widget = QWidget()
        middle_layout = QVBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        # 添加检索栏
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        # 行人ID搜索
        self.id_label = QLabel("行人ID:")
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("输入行人ID")
        
        # 朝向选择
        self.orientation_label = QLabel("朝向:")
        self.orientation_combo = QComboBox()
        self.orientation_combo.addItems(["全部", "正面", "背面", "左侧", "右侧"])
        
        # 搜索按钮
        self.search_btn = QPushButton("搜索")
        self.search_btn.clicked.connect(self.on_search)
        
        # 添加到检索栏布局
        search_layout.addWidget(self.id_label)
        search_layout.addWidget(self.id_input)
        search_layout.addWidget(self.orientation_label)
        search_layout.addWidget(self.orientation_combo)
        search_layout.addWidget(self.search_btn)
        search_layout.addStretch()
        
        # 顶部工具栏
        self.toolbar = QToolBar()
        self.toolbar.setIconSize(QSize(24, 24))
        
        # 添加工具栏按钮
        self.btn_prev = QPushButton("上一张")
        self.btn_next = QPushButton("下一张")
        self.btn_zoom_in = QPushButton("放大")
        self.btn_zoom_out = QPushButton("缩小")
        self.btn_fit = QPushButton("适应窗口")
        
        self.toolbar.addWidget(self.btn_prev)
        self.toolbar.addWidget(self.btn_next)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.btn_zoom_in)
        self.toolbar.addWidget(self.btn_zoom_out)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.btn_fit)
        
        # 连接按钮信号
        self.btn_prev.clicked.connect(self.show_previous_image)
        self.btn_next.clicked.connect(self.show_next_image)
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_fit.clicked.connect(self.fit_to_window)
        
        # 图片显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setBackgroundRole(QPalette.Dark)
        self.scroll_area.setWidgetResizable(True)
        
        # 创建网格布局容器
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(10)  # 设置网格间距
        
        # 第一行： ref, smplx, back, fore
        self._img_label_tgt = self._get_img_label() 
        self.grid_layout.addWidget(self._img_label_tgt, 0, 0)  # row, col, rowspan, colspan
        self._img_label_smplx = self._get_img_label()
        self.grid_layout.addWidget(self._img_label_smplx, 0, 1)
        self._img_label_background = self._get_img_label()
        self.grid_layout.addWidget(self._img_label_background, 0, 2)
        self._img_label_foreground = self._get_img_label()
        self.grid_layout.addWidget(self._img_label_foreground, 0, 3)

        self._img_label_ref_list = []
        # 右侧四张图片，2x2
        for i in range(4):
            image_label = self._get_img_label() 
            self._img_label_ref_list.append(image_label)
            self.grid_layout.addWidget(image_label, 1, i)  # (1,0),(1,1),(1,2),(1,3)
        
        self.scroll_area.setWidget(self.grid_widget)
        
        # 右侧区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_splitter = QSplitter(Qt.Vertical)

        # Top widget with combo box and tree view
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0,0,0,0)
        self.orientation_combo_right = QComboBox()
        self.orientation_combo_right.addItems(["front", "back", "left", "right"])
        self.orientation_combo_right.currentIndexChanged.connect(self.on_orientation_changed)
        top_layout.addWidget(self.orientation_combo_right)
        self.right_top_tree_view = QTreeView()
        self.right_top_tree_model = QStandardItemModel()
        self.right_top_tree_model.setHorizontalHeaderLabels(["文件名"])
        self.right_top_tree_view.setModel(self.right_top_tree_model)
        self.right_top_tree_view.clicked.connect(self.on_right_top_tree_view_clicked)
        top_layout.addWidget(self.right_top_tree_view)
        right_splitter.addWidget(top_widget)

        # Middle widget for image preview
        self._img_label_right_preview = self._get_img_label()
        self._img_label_right_preview.setText("点击上方列表中的图片进行预览")
        right_splitter.addWidget(self._img_label_right_preview)

        # Bottom widget for attributes of the PREVIEWED image
        self.right_attr_tree_view = QTreeView()
        self.right_attr_tree_model = QStandardItemModel()
        self.right_attr_tree_model.setHorizontalHeaderLabels(["属性", "值"])
        self.right_attr_tree_view.setModel(self.right_attr_tree_model)
        self.right_attr_delegate = AttributeDelegate(self)
        self.right_attr_tree_view.setItemDelegateForColumn(1, self.right_attr_delegate)
        right_splitter.addWidget(self.right_attr_tree_view)
        
        right_splitter.setSizes([300, 300, 200]) # Initial sizes
        right_layout.addWidget(right_splitter)

        # 添加到中间布局
        middle_layout.addWidget(search_widget)
        middle_layout.addWidget(self.toolbar)
        middle_layout.addWidget(self.scroll_area)
        
        # 添加所有部件到分割器
        splitter.addWidget(middle_widget)
        splitter.addWidget(right_widget)
        
        # 设置分割比例
        splitter.setSizes([300, 600, 300])
        
        # 主布局
        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)
    
    def on_search(self):
        """处理搜索按钮点击事件"""
        person_id = self.id_input.text()
        orientation = self.orientation_combo.currentText()
        
        # 这里可以添加搜索逻辑
        self.statusBar().showMessage(f"搜索条件: ID={person_id}, 朝向={orientation}")
    
    def on_tree_view_person_clicked(self, index):
        """点击左侧person id节点"""
        try:
            id_person = self.person_model.itemFromIndex(index).text()
            if not self._dataset:
                QMessageBox.warning(self, "警告", "数据集未初始化")
                return
            
            person = self._dataset.get_person(id_person)
            self._person_selected = person
            self.statusBar().showMessage(f"选中行人ID: {id_person}")
            
            # 清空并填充详情视图
            self.detail_model.clear()
            self.detail_model.setHorizontalHeaderLabels(["图片"])
            
            keys_img = person.get_img_set_keys()
            # 这里添加具体ID下的图片列表（示例数据）
            for key in keys_img:
                item = QStandardItem(key)
                self.detail_model.appendRow(item)
            
            # 显示返回按钮并切换到详情视图
            self.btn_back.setVisible(True)
            self.left_stack.setCurrentIndex(1)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载行人信息失败: {str(e)}")
            print(f"加载行人信息错误: {traceback.format_exc()}")
    

    def on_detail_view_clicked(self, index):
        """点击详情视图中的图片项"""
        try:
            name_img = self.detail_model.itemFromIndex(index).text()
            if not self._person_selected:
                QMessageBox.warning(self, "警告", "未选择行人")
                return
                
            self._img_tgt = self._person_selected[name_img]
            self.left_attr_delegate.img_obj = self._img_tgt
            self._imgList_matched_dict = None # Reset
            
            # --- Clear right panel ---
            self.right_top_tree_model.clear()
            self.right_top_tree_model.setHorizontalHeaderLabels(["文件名"])
            self.right_attr_tree_model.clear()
            self.right_attr_tree_model.setHorizontalHeaderLabels(["属性", "值"])
            self._img_label_right_preview.clear()
            self._img_label_right_preview.setText("点击上方列表中的图片进行预览")
            self._img_previewed_right = None
            self.right_attr_delegate.img_obj = None

            # --- Populate bottom-left view (Main Image Attributes) ---
            self._populate_attribute_view(self.left_attr_tree_model, self._img_tgt)


            (
                img_ref_list,
                _,
                imgList_matched_dict
            ) = self._person_selected._get_imgList_from_img_set(
                stage=1,
                idx_img_tgt=name_img,
                is_discard=False,
            )
            self._imgList_matched_dict = imgList_matched_dict

            # --- Populate top view (Files) based on current combo box selection ---
            self.on_orientation_changed(self.orientation_combo_right.currentIndex())

            self._img_ref_list = img_ref_list
            self.statusBar().showMessage(f"选中图片: {name_img}")
            # 展示选中的图片为5张图片
            self.load_image()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载图片失败: {str(e)}")
            print(f"加载图片错误: {traceback.format_exc()}")

    def on_orientation_changed(self, index):
        """Handle orientation selection change for the right panel."""
        self.right_top_tree_model.clear()
        self.right_top_tree_model.setHorizontalHeaderLabels(["文件名"])
        self._img_label_right_preview.clear()
        self._img_label_right_preview.setText("点击上方列表中的图片进行预览")

        if not hasattr(self, '_imgList_matched_dict') or not self._imgList_matched_dict:
            return

        orientation = self.orientation_combo_right.itemText(index)
        img_list = self._imgList_matched_dict.get(orientation, [])
        
        if img_list:
            for img_item in img_list:
                try:
                    name = img_item.get_name_img()
                    item_child = QStandardItem(name)
                    item_child.setData(img_item, Qt.UserRole) # Associate Img object
                    item_child.setEditable(False)
                    self.right_top_tree_model.appendRow(item_child)
                except Exception as e:
                    print(f"Error getting img name for {orientation}: {e}")

    def on_right_top_tree_view_clicked(self, index):
        """Click on an image in the top right list to preview."""
        try:
            item = self.right_top_tree_model.itemFromIndex(index)
            if item:
                img_data = item.data(Qt.UserRole)
                if img_data: # Check if Img object is associated
                    self._img_previewed_right = img_data
                    self.right_attr_delegate.img_obj = img_data
                    self._set_pixmap(img=img_data, type_img="reid", label=self._img_label_right_preview)
                    # Populate attributes for the previewed image
                    self._populate_attribute_view(self.right_attr_tree_model, img_data)
        except Exception as e:
            QMessageBox.warning(self, "预览失败", f"无法加载图片预览: {str(e)}")
            print(f"预览图片错误: {traceback.format_exc()}")

    def on_back_clicked(self):
        """点击返回按钮"""
        self.left_stack.setCurrentIndex(0)  # 返回到ID列表
        self.btn_back.setVisible(False)  # 隐藏返回按钮
    
    def get_image_files(self, folder):
        """获取文件夹中的所有图片文件"""
        extensions = ('.jpg', '.png', '.bmp', '.gif')
        image_files = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file.lower().endswith(extensions):
                    image_files.append(os.path.join(root, file))
        return sorted(image_files)
    
    def _set_pixmap(self, img, type_img, label):
        try:
            if img is None:
                label.setText("无对应视角")
                return
            path_img = img.get_path(type_img)
            pixmap_img = QPixmap(path_img)
            if pixmap_img.isNull():
                label.setText("无法加载图片")
                return
            name_img = os.path.basename(path_img)
            label.setPixmap(pixmap_img)
            label.scale_factor = self.scale_factor
            label.setImageName(name_img)  # 设置图片名
            label.adjustSize()
        except Exception as e:
            label.setText(f"加载失败: {str(e)}")
            print(f"设置图片错误: {traceback.format_exc()}")

    def load_image(self):
        """加载并显示图片"""
        try:
            if not self._img_tgt:
                self.statusBar().showMessage("未选择目标图片")
                return
                            
            # 加载目标图片的四种视角
            self._set_pixmap(img=self._img_tgt, type_img="reid", label=self._img_label_tgt)
            self._set_pixmap(img=self._img_tgt, type_img="smplx_guidance", label=self._img_label_smplx)
            self._set_pixmap(img=self._img_tgt, type_img="background", label=self._img_label_background)
            self._set_pixmap(img=self._img_tgt, type_img="foreground", label=self._img_label_foreground)
            
            # 加载参考图片列表
            for (img, label) in zip(self._img_ref_list, self._img_label_ref_list):
                self._set_pixmap(img=img, type_img="reid", label=label)
            
            # 更新状态栏
            if hasattr(self._img_tgt, 'get_path'):
                try:
                    path_tgt = self._img_tgt.get_path("reid")
                    name_img = os.path.basename(path_tgt)
                    self.statusBar().showMessage(f"已加载: {name_img}")
                except:
                    self.statusBar().showMessage("图片加载完成")
            else:
                self.statusBar().showMessage("图片加载完成")
                
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载图片失败: {str(e)}")
            print(f"load_image错误: {traceback.format_exc()}")
    
    def show_previous_image(self):
        """显示上一张图片"""
        if not self.image_files or self.current_image_index <= 0:
            return
        
        self.current_image_index -= 1
        self.current_image_path = self.image_files[self.current_image_index]
        self.load_image(self.current_image_path)
    
    def show_next_image(self):
        """显示下一张图片"""
        if not self.image_files or self.current_image_index >= len(self.image_files) - 1:
            return
        
        self.current_image_index += 1
        self.current_image_path = self.image_files[self.current_image_index]
        self.load_image(self.current_image_path)
    
    def zoom_in(self):
        """放大图片"""
        self.scale_image(1.25)
    
    def zoom_out(self):
        """缩小图片"""
        self.scale_image(0.8)
    
    def scale_image(self, factor):
        """缩放图片"""
        if not hasattr(self, 'original_pixmap') or self.original_pixmap.isNull():
            return
            
        self.scale_factor *= factor
        self.update_display_image()
    
    def update_display_image(self):
        """更新显示的图片（应用缩放和旋转）"""
        transform = QTransform()
        transform.scale(self.scale_factor, self.scale_factor)
        
        self.display_pixmap = self.original_pixmap.transformed(
            transform, Qt.SmoothTransformation)
        
        # 更新所有标签的显示
        for label in self.image_labels:
            label.setPixmap(self.display_pixmap)
            label.scale_factor = self.scale_factor
            label.adjustSize()
        
        # 调整滚动条位置
        self.adjust_scroll_bar(self.scroll_area.horizontalScrollBar(), 1.0)
        self.adjust_scroll_bar(self.scroll_area.verticalScrollBar(), 1.0)
    
    def adjust_scroll_bar(self, scroll_bar, factor):
        """调整滚动条位置"""
        scroll_bar.setValue(int(factor * scroll_bar.value() + ((factor - 1) * scroll_bar.pageStep() / 2)))
    
    def fit_to_window(self):
        """适应窗口大小"""
        if not hasattr(self, 'original_pixmap') or self.original_pixmap.isNull():
            return
        
        # 计算缩放比例
        viewport_size = self.scroll_area.viewport().size()
        pixmap_size = self.original_pixmap.size()
        
        scale_factor = min(viewport_size.width() / pixmap_size.width(),
                          viewport_size.height() / pixmap_size.height())
        
        self.scale_factor = scale_factor
        self.update_display_image()
    
    def set_root_path(self, path):
        """设置文件浏览器的根路径"""
        if os.path.exists(path):
            self.default_path = path
            self.file_model.setRootPath(path)
            self.tree_view.setRootIndex(self.file_model.index(path))
            self.current_folder = path
            self.image_files = self.get_image_files(path)
            if self.image_files:
                self.current_image_index = 0
                self.current_image_path = self.image_files[0]
                self.load_image(self.current_image_path)
        else:
            self.statusBar().showMessage(f"路径不存在: {path}")
    
    def closeEvent(self, event):
        """重写关闭事件，确保程序正常退出"""
        try:
            # 停止定时器
            if hasattr(self, 'timer'):
                self.timer.stop()
            
            # 清理资源
            if hasattr(self, '_dataset'):
                del self._dataset
            
            event.accept()
        except Exception as e:
            print(f"关闭事件错误: {traceback.format_exc()}")
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # 设置应用程序属性，确保正常退出
    app.setQuitOnLastWindowClosed(True)
    
    try:
        viewer = ImageViewer()
        
        # 如果命令行参数提供了路径，则使用该路径
        if len(sys.argv) > 1:
            viewer.set_root_path(sys.argv[1])
        
        viewer.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"程序启动错误: {traceback.format_exc()}")
        sys.exit(1)