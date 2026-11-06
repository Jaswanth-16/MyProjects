from PIL import Image
from scene_art import generate_scene
import pytest


def test_six_scenes_are_distinct(tmp_path):
    images = []
    for i in range(1, 7):
        path = generate_scene(i, tmp_path / f'{i}.png')
        with Image.open(path) as im:
            assert im.size == (720, 1280)
            images.append(im.getpixel((400, 200)))
    assert len(set(images)) > 1


def test_reject_unsupported_scene(tmp_path):
    with pytest.raises(ValueError):
        generate_scene(7, tmp_path / 'bad.png')
