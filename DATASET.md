# Dataset provenance and attribution

This project uses the World Bank's World Development Indicators (WDI), dataset ID `0037712`.
The checked-in snapshot contains 2022 observations for `NY.GDP.PCAP.CD` and `SP.POP.TOTL`,
downloaded from the official V2 Indicators API. The snapshot is an offline copy for reproducibility.

- Catalog: https://datacatalog.worldbank.org/search/dataset/0037712/world-development-indicators
- API documentation: https://datahelpdesk.worldbank.org/knowledgebase/articles/889392
- Dataset license in catalog metadata: Creative Commons Attribution 4.0
- License page: https://datacatalog.worldbank.org/public-licenses?fragment=cc
- Attribution: **World Bank, World Development Indicators (CC BY 4.0).**

The API response can include aggregate regions as well as countries/economies. StatsDesk retains
the region field in the source snapshot and excludes `Aggregates` records according to the
pre-analysis plan. Missing values are retained as blank fields and are not imputed.

`data/dataset_metadata.json` records when this copy was retrieved, the API update metadata, exact
source URLs, and the SHA-256 digest of `data/wdi_2022.csv`. Always verify that digest before
interpreting or reusing derived reports.

World Bank data can be updated upstream. The committed snapshot is not a promise that a later API
response will reproduce the same statistics. Refreshing it generates new metadata and a new digest.
