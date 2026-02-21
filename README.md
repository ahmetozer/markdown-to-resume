# Markdown to Resume

Convert a Markdown resume into a styled PDF and deploy it to GitHub Pages.

## How It Works

1. Write your resume in `resume.md`
2. `resume_to_pdf.py` converts it into a professionally formatted PDF using ReportLab
3. `index.html` provides a web viewer with an embedded PDF preview and download link
4. A GitHub Actions workflow builds the PDF and deploys everything to GitHub Pages on every push

## Local Build

```bash
pip install -r requirements.txt
python resume_to_pdf.py resume.md resume.pdf
```

## CI/CD

The included GitHub Actions workflow (`.github/workflows/resume.yml`) automatically:

- Builds the PDF from `resume.md`
- Deploys to GitHub Pages

Triggers on pushes to `main` that modify `resume.md`, `resume_to_pdf.py`, `index.html`, `requirements.txt`, or the workflow file. Can also be triggered manually via `workflow_dispatch`.

### Setup

Set **Settings > Pages > Source** to **GitHub Actions** in your repository.

## Project Structure

```
resume.md              # Resume content in Markdown
resume_to_pdf.py       # Markdown-to-PDF converter (ReportLab)
index.html             # Web viewer for the PDF
requirements.txt       # Python dependencies
.github/workflows/     # CI/CD pipeline
```

## License

See [LICENSE](LICENSE) for details.
