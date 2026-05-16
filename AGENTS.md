# Repository Guidelines

## Project Goal

EasyPhysics is building an accessible, concept-first explanation of fundamental physics. In a Feynman-like style, advanced physics concepts should be stripped of jargon and put into a curriculum understandable by motivated high-schoolers or college freshmen. The project emphasizes meaning before jargon, careful scientific claims, gentle math, and a connected wiki structure that helps curious learners see how physics ideas fit together.

## Encoding and File Safety

All text files in this repository must be UTF-8 without BOM.

When reading or writing files on Windows, preserve UTF-8 exactly. Do not reinterpret files as Windows-1252, CP1252, Latin-1, or OEM code pages.

Avoid smart punctuation in generated text unless explicitly requested:

- Use ASCII apostrophe (`'`) instead of curly apostrophe (`U+2019`).
- Use ASCII double quote (`"`) instead of curly double quotes (`U+201C` or `U+201D`).
- Use `--` or `-` instead of em dash (`U+2014`).
- Use `...` instead of ellipsis (`U+2026`).

Before editing a file that appears to contain mojibake patterns such as `U+00E2`, `U+00C3`, or `U+00EF` appearing where punctuation or accented text should be, do not fix the content blindly. First inspect the file encoding and confirm whether the visible text is already corrupted or merely being decoded incorrectly.
