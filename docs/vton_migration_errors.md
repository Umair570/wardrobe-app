# Modal Native VTON Migration: Error & Solution Reference

This document outlines the major errors encountered during the migration of the Virtual Try-On pipeline from Hugging Face proxies to a custom Native GPU environment on Modal.com, why they occurred, and how we solved them. Consider this a technical post-mortem reference!

---

### 1. Gradio Rate Limits / ZeroGPU Allocation Errors
*   **Error Context:** The application repeatedly hung or crashed with "Quota Exceeded" or "ZeroGPU allocation limits" during peak usage.
*   **Root Cause:** Free public HuggingFace spaces throttle programmatic API calls strictly. ZeroGPU dynamically unloads models to manage global demand, causing unpredictable scaling limits.
*   **Solution:** We completely severed ties with public Gradio spaces. We provisioned a custom backend on **Modal** running an A10G Cloud GPU to host and run the FASHN-VTON models privately, ensuring 100% uptime and un-throttled execution.

---

### 2. HuggingFace Hub "Access Denied" / Gated Repository Errors
*   **Error Context:** When Modal attempted to download the FASHN-VTON weights, it threw `Access Denied for Kwai-Kolors/Kolors`.
*   **Root Cause:** Some cutting-edge machine learning repositories are "Gated", meaning you must explicitly agree to the license terms on Hugging Face before pulling them. Automated downloader scripts without credentials get rejected entirely.
*   **Solution:** We linked your local environment's `HF_TOKEN` directly into Modal's cloud secrets. This allowed the cloud environment to securely read the token and bypass the permissions barrier dynamically.

---

### 3. Missing DWPose ONNX Weight Components
*   **Error Context:** Inference on Modal would abruptly crash with `FileNotFoundError: dwpose/yolox_l.onnx`.
*   **Root Cause:** The underlying architecture of Fashn-VTON relies on rigid human-pose estimation files (DWPose and YoloX). Those standard weights are not fundamentally packaged inside Diffusers, meaning the standard pipeline loader crashed.
*   **Solution:** We manually injected download logic into the Modal script to explicitly fetch `yolox_l.onnx` and `dw-ll_ucoco_384.onnx` from Hugging Face and load them onto the persistent Modal Volume before the model even executes.

---

### 4. PyTorch `DTensor` Compatibility Crash (ImportError)
*   **Error Context:** Start-up crashes citing `ImportError: cannot import name 'DTensor' from 'torch.distributed.tensor'`.
*   **Root Cause:** Cutting-edge Python dependencies often break backwards compatibility. Modal defaults to pulling the absolute latest PyTorch (v2.4.0+), which had fundamentally re-written specific tensor distribution structures that `transformers` was still expecting.
*   **Solution:** We hardcoded and locked the Modal container environment strictly to `torch==2.3.0` and `transformers==4.40.1`. Pinning dependencies to known-working matrices completely fixed the internal mismatches.

---

### 5. Cross-Cloud Networking Crash (Localhost URLs)
*   **Error Context:** VTON inference completely failed and threw `httpx ValueError: embedded null byte` or internal Timeout errors during testing.
*   **Root Cause:** The local backend (Uvicorn) was telling the Cloud GPU to essentially download a picture from `http://127.0.0.1:8000/uploads/...`. But because Modal is a Linux server in the cloud, its definition of `127.0.0.1` is itself, not your laptop! It tried to ping an invisible server and crashed out.
*   **Solution:** We re-wrote the transfer architecture. Instead of forcing Modal to parse URLs, the local backend physically reads the bytes from your hard drive, mathematically encodes them into `Base64` chunks, and sends the raw file payload directly to Modal via JSON.

---

### 6. FastAPI Schema Validation Failure (422 Unprocessable Entity)
*   **Error Context:** We saw `Modal API Validation Error: 422 Unprocessable Entity` instantly upon clicking the button.
*   **Root Cause:** When we implemented the `Base64` transfer (Solution 5), we updated the local Uvicorn backend to map the string as `person_image_b64`. However, we forgot to execute `modal deploy`, meaning the Modal Cloud server still strictly demanded the old key (`person_image_url`). FastAPI automatically throws `422` if required schema fields are missing.
*   **Solution:** We executed `modal deploy modal_infrastructure/vton_server.py` to synchronize the python Schema parameters inside the cloud container natively, matching exactly what the frontend pushed.

---

### 7. Broken `<img src="">` Tag Masking (Prefix Corruption)
*   **Error Context:** Everything in the logs succeeded perfectly with HTTP `200 OK`, but the user interface just displayed a tiny broken image icon.
*   **Root Cause:** A helper function inside the Uvicorn endpoint (`_to_absolute_url()`) was rigorously programmed to enforce URL completeness. If a string did not start with `http://`, it assumed the string was a database pointer and forcibly prepended `http://localhost:8000/`. Consequently, it corrupted the native DOM image MIME protocol by generating `http://localhost:8000/data:image/png;base64...` which browsers refuse to compute.
*   **Solution:** We bypassed the protocol formatting implicitly inside Python by checking if the URL `.startswith("data:")`. This prevented Uvicorn from modifying pristine Base64 binary packets.
