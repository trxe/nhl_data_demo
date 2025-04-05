# NHL data playground project

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Getting files and composing into csv

```bash
python ./tools/downloader.py -post # defaults to output in ./data_json
# will query for date range of inputs and teams to filter by

./data/combine_outputs.sh games ./tools/ ./data_json/ ./data/ del
./data/combine_outputs.sh shifts ./tools/ ./data_json/ ./data/ del
./data/combine_outputs.sh rosters ./tools/ ./data_json/ ./data/ del
./data/combine_outputs.sh plays ./tools/ ./data_json/ ./data/ keep
./data/combine_outputs.sh play_details ./tools/ ./data_json/ ./data/ del
```

### Project files

| File name | description |
| --------- | ----------- |
| `/tools/database.py` | custom postgres adapter |
| `/tools/nhl_api.py` | nhl api handles |
| `/tools/downloader.py` | small script to pull raw data from nhl_api |
| `/tools/transform.py` | transforms data into format for SQL entry (WIP) |
| `/match_shifts.ipynb` | calculating corsi/fenwick (playing with data from 2024-25 season) |
| `/draw.py` | draws a rink, extracted from `match_shifts` |
| `/xgoals.py` | [WIP] some data exploration and attempting a log regression xgoals model |

## Other stuff

I have made a simple view of shift charts overlaid with game events here too:

```
https://stats.cap-sized.com/<gameid>

e.g. https://stats.cap-sized.com/2023020573
```