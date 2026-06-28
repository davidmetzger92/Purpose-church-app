# Purpose Church QR code

Branded QR code that opens the app home page: **https://app.purposearizona.com**

| File | Use |
|------|-----|
| `purpose-qr.png` | High-res (2048×2048) raster — flyers, slides, printed handouts |
| `purpose-qr.svg` | Vector — scales to any size with no quality loss (large banners, signage) |

The "P" mark sits in the center and the QR uses high error-correction, so it stays
scannable even with the logo overlay. **Always test-scan after printing.**

## Regenerating

Edit the URL/colors/logo in `scripts/generate-qr.py`, then:

```bash
pip install segno pillow
python3 scripts/generate-qr.py
```
