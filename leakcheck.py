import argparse
import csv
from pathlib import Path

import imagehash
from PIL import Image

IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp"}


def hash_folder(folder):
    hashes = {}
    for path in Path(folder).rglob("*"):
        if path.suffix.lower() in IMAGE_TYPES:
            try:
                with Image.open(path) as img:
                    hashes[path] = imagehash.phash(img)
            except Exception as e:
                print(f"skipped {path.name}: {e}")
    return hashes


class BKTree:
    """Tree for fast 'find the closest fingerprint within distance d' search."""

    def __init__(self):
        self.root = None  # each node: (hash, path, children)

    def add(self, h, path):
        if self.root is None:
            self.root = (h, path, {})
            return
        node = self.root
        while True:
            d = h - node[0]
            child = node[2].get(d)
            if child is None:
                node[2][d] = (h, path, {})
                return
            node = child

    def search(self, h, threshold):
        if self.root is None:
            return None
        best = None
        stack = [self.root]
        while stack:
            node_hash, node_path, children = stack.pop()
            d = h - node_hash
            if d <= threshold and (best is None or d < best[1]):
                best = (node_path, d)
            # triangle inequality: only these branches can contain matches
            for child_d, child in children.items():
                if d - threshold <= child_d <= d + threshold:
                    stack.append(child)
        return best


def find_leaks(train_dir, test_dir, threshold=5):
    print("Fingerprinting train images...")
    train = hash_folder(train_dir)
    print("Fingerprinting test images...")
    test = hash_folder(test_dir)

    tree = BKTree()
    for train_path, train_hash in train.items():
        tree.add(train_hash, train_path)

    leaks = []
    for test_path, test_hash in test.items():
        match = tree.search(test_hash, threshold)
        if match:
            train_path, distance = match
            leaks.append((test_path, train_path, distance))
    return leaks, len(test)


def save_csv(leaks, csv_path):
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["test_image", "train_image", "distance"])
        for test_path, train_path, distance in leaks:
            writer.writerow([test_path, train_path, distance])


def save_pairs(leaks, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    for i, (test_path, train_path, distance) in enumerate(leaks):
        with Image.open(test_path) as a, Image.open(train_path) as b:
            left = a.convert("RGB").resize((256, 256))
            right = b.convert("RGB").resize((256, 256))
        pair = Image.new("RGB", (520, 256), "white")
        pair.paste(left, (0, 0))
        pair.paste(right, (264, 0))
        pair.save(out / f"leak_{i}_{test_path.stem}.png")


def main():
    parser = argparse.ArgumentParser(
        description="Find images that appear in both train and test folders."
    )
    parser.add_argument("train", help="train folder")
    parser.add_argument("test", help="test folder")
    parser.add_argument("--threshold", type=int, default=5,
                        help="0 = exact match only, higher = looser (default 5)")
    parser.add_argument("--csv", help="save the leak list to this CSV file")
    parser.add_argument("--show", help="save side-by-side leak images to this folder")
    args = parser.parse_args()

    leaks, total = find_leaks(args.train, args.test, args.threshold)

    for test_path, train_path, distance in leaks:
        print(f"LEAK  {test_path.name}  ~  {train_path.name}  (distance {distance})")

    percent = 100 * len(leaks) / total if total else 0
    print(f"\n{len(leaks)} of {total} test images ({percent:.1f}%) also appear in train.")

    if args.csv:
        save_csv(leaks, args.csv)
        print(f"Saved leak list to {args.csv}")
    if args.show:
        save_pairs(leaks, args.show)
        print(f"Saved side-by-side images to {args.show}/")


if __name__ == "__main__":
    main()
    