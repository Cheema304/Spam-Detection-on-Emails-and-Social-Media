# Dataset Sources and Attribution

## Email: Apache SpamAssassin Public Corpus
Project source index:
https://spamassassin.apache.org/old/publiccorpus/

Files used by the project:
- `20030228_easy_ham.tar.bz2`
- `20030228_spam.tar.bz2`

The project parses the email Subject and textual body and excludes attachments from the classifier input.

## Social Media: UCI YouTube Spam Collection
UCI Machine Learning Repository dataset page:
https://archive.ics.uci.edu/dataset/380/youtube+spam+collection

Citation:
Alberto, T. C., & Lochter, J. V. (2015). *YouTube Spam Collection* [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C58885

License listed by UCI: CC BY 4.0.

## Reproducibility
The project stores the SHA-256 hash of the generated combined dataset in `model/metadata.json`. Re-running `scripts/fetch_real_data.py --force` rebuilds the dataset from the listed public sources.
