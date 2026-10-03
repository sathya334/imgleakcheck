import random

import imagehash
from PIL import Image, ImageDraw

from leakcheck import BKTree, find_leaks


def make_image(seed):
    rng = random.Random(seed)
    color = lambda: tuple(rng.randint(0, 255) for _ in range(3))
    img = Image.new("RGB", (256, 256), color())
    draw = ImageDraw.Draw(img)
    for _ in range(8):
        x1, y1 = rng.randint(0, 200), rng.randint(0, 200)
        x2, y2 = x1 + rng.randint(20, 100), y1 + rng.randint(20, 100)
        if rng.random() < 0.5:
            draw.rectangle([x1, y1, x2, y2], fill=color())
        else:
            draw.ellipse([x1, y1, x2, y2], fill=color())
    return img


def make_folders(tmp_path):
    train, test = tmp_path / "train", tmp_path / "test"
    train.mkdir()
    test.mkdir()
    return train, test


def test_finds_exact_copy(tmp_path):
    train, test = make_folders(tmp_path)
    img = make_image(1)
    img.save(train / "a.png")
    img.save(test / "a_copy.png")
    leaks, total = find_leaks(train, test)
    assert len(leaks) == 1 and total == 1


def test_finds_resized_renamed_jpg(tmp_path):
    train, test = make_folders(tmp_path)
    img = make_image(2)
    img.save(train / "original.png")
    img.resize((150, 150)).save(test / "different_name.jpg", quality=80)
    leaks, _ = find_leaks(train, test)
    assert len(leaks) == 1


def test_different_images_are_not_leaks(tmp_path):
    train, test = make_folders(tmp_path)
    for i in range(10):
        make_image(i).save(train / f"{i}.png")
    for i in range(100, 110):
        make_image(i).save(test / f"{i}.png")
    leaks, total = find_leaks(train, test)
    assert leaks == [] and total == 10


def test_bktree_matches_brute_force():
    rng = random.Random(0)
    to_hash = lambda n: imagehash.hex_to_hash(f"{n:016x}")
    numbers = [rng.getrandbits(64) for _ in range(300)]
    hashes = [to_hash(n) for n in numbers]

    tree = BKTree()
    for i, h in enumerate(hashes):
        tree.add(h, i)

    for _ in range(100):
        query = rng.choice(numbers)
        for bit in rng.sample(range(64), rng.randint(0, 8)):
            query ^= 1 << bit  # flip a few bits
        q = to_hash(query)
        best = min(q - h for h in hashes)  # slow, guaranteed-correct answer
        result = tree.search(q, 10)
        assert result is not None and result[1] == best