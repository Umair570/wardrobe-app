# Wardrobe AI

AI-powered wardrobe management application.

---

## Team

- Umair — Segmentation & Classification
- Mahad — Backend & Database
- Ayesha — Frontend
- Abdulrehman — Chatbot & Visualization

---

## Project Structure

```
backend/
frontend/
ml/
docs/
```

---

## ML Pipeline

```
Input Image
      │
      ▼
SegFormer
      │
      ▼
Segmentation Mask
      │
      ▼
Transparent PNG
```

---

## Run

Install packages

```bash
pip install -r requirements.txt
```

Place images inside

```
ml/test_images/
```

Outputs will be saved inside

```
ml/outputs/
```

---

## Model

```
mattmdjaga/segformer_b2_clothes
```

---

## Current Progress

### Day 1

- Load pretrained SegFormer
- Generate segmentation mask
- Remove background
- Save transparent PNG

### Day 2

- Classification
- Backend Integration

### Day 3

- Testing
- Optimization