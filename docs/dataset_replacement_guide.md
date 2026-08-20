# Real Dataset Pipeline

The project now uses a reproducible real-data acquisition process rather than bundled synthetic benchmark data.

## Email source
Apache SpamAssassin Public Corpus:
- `20030228_easy_ham.tar.bz2`
- `20030228_spam.tar.bz2`

The parser extracts email subject and textual body while ignoring attachments.

## Social-media source
UCI YouTube Spam Collection (DOI `10.24432/C58885`, CC BY 4.0). The project combines the five labelled YouTube comment CSV files.

## Combined schema
`text,label,source,dataset`

`source` is explicitly either `Email` or `Social Media`, enabling source-aware evaluation.

## Rebuild
```bash
python scripts/fetch_real_data.py --force
python scripts/train.py
```

All benchmark metrics are recalculated from the current combined dataset. Do not manually type evaluation numbers into the UI.
