import os

from PIL import Image
import importlib

from .set_base import SetBase
from ..object import Img
from ..object import Person

class PersonSet(SetBase):
    def __init__(self) -> None:
        super().__init__()

    def __len__(self):
        """Return the number of persons in the set."""
        return len(self._list)


    def add_person(self, person):
        if person in self._dict:
            raise("person_set:person already in dict!")
        self.add_item(person.get_id(), person)

    def _add_img(self, img:Img):
        """Add an image to the person set, creating a new person if necessary."""
        key_person = img.get_key_person()
        if key_person not in self._dict:
            if img.is_video() or img.is_smplx():
                person = Person(key_person)
                person.add_img(img)
                self._list.append(person)
                self._dict[key_person] = person
        else:
            person = self._dict[key_person]
            person.add_img(img)

    def check_empty_item(self):
        for person in self._list:
            if person.is_img_set_empty():
                self._list.remove(person)
                self._dict.pop(person.get_id())


    