import random
from pathlib import Path

from PIL import Image, ImageDraw

random.seed(42)
train_dir = Path("demo/train")
test_dir = Path("demo/test")
train_dir.mkdir(parents=True, exist_ok=True)
test_dir.mkdir(parents=True, exist_ok=True)


def random_color():
    return tuple(random.randint(0, 255) for _ in range(3))


def random_image():
    img = Image.new("RGB", (256, 256), random_color())
    draw = ImageDraw.Draw(img)
    for _ in range(8):
        x1, y1 = random.randint(0, 200), random.randint(0, 200)
        x2, y2 = x1 + random.randint(20, 100), y1 + random.randint(20, 100)
        shape = random.choice([draw.rectangle, draw.ellipse])
        shape([x1, y1, x2, y2], fill=random_color())
    return img


# 50 train images
train_images = []
for i in range(50):
    img = random_image()
    img.save(train_dir / f"train_{i}.png")
    train_images.append(img)

# 20 normal test images
for i in range(20):
    random_image().save(test_dir / f"test_{i}.png")

# 5 sneaky leaks: train images resized, renamed, saved as JPG
for i in range(5):
    leaked = train_images[i].resize((200, 200))
    leaked.save(test_dir / f"leaked_{i}.jpg", quality=85)

print("Done: 50 train images, 25 test images (5 are hidden leaks)")