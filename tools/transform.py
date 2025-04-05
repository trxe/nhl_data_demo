import polars as pl
import os
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Optional, Callable
import yaml
import json
import argparse
import datetime as dt
from pathlib import Path
from logger import Logger

class MappingAction:
    mapping: dict[str, Callable] = {}

    @classmethod
    def register(cls, func: Callable):
        cls.mapping[func.__name__] = func

    @classmethod
    def take(cls, key):
        return cls.mapping[key]

def regact(func):
    MappingAction.register(func)

@regact
def concat_string(a: str, b: str, delim: str = " "):
    return f"{a}{delim}{b}"

def fmt_date(val: dt.date, fmt: str = '%Y-%m-%d') -> str:
    return val.strftime(fmt)

class Mapping:
    def __init__(self, keyto: str, fromdef: str | dict):
        self.keyto: str = keyto
        self.keyfrom: Optional[str] = None
        self.action: Optional[Callable] = None
        self.args: Optional[list] = None
        self.kwargs: Optional[dict] = None
        if isinstance(fromdef, str):
            self.keyfrom = fromdef.split('.')
        else:
            self.action = fromdef.get('action')
            self.args = fromdef.get('args')
            self.kwargs = fromdef.get('kwargs')
    
    def map(self, inputv: dict) -> tuple[str, any]:
        if self.action:
            return self.keyto, self.action([
                inputv.get(arg)
                for arg in self.args
            ], **self.kwargs)
        if self.keyfrom:
            val = inputv
            for key in self.keyfrom:
                key = self.keyto if key == '+' else key
                val = val.get(key, {})
            return self.keyto, val if val != {} else None
        return self.keyto, inputv.get(self.keyto)


class Flatten:
    def __init__(self, fromdef: dict):
        self.key = fromdef['_key']
        self.mappings = []
        for key, value in fromdef.items():
            if key == '_key':
                continue
            self.mappings.append(Mapping(key, value))

    def flatten(self, inputv: dict) -> list[dict[str, any]]:
        returnlist = inputv.get(self.key)
        const_mappings_list = [mapping.map(inputv) for mapping in self.mappings]
        const_mappings = {k:v for k, v in const_mappings_list}
        return [ {**item, **const_mappings} for item in returnlist ]


class RuleMap:
    def __init__(self, config_fp: str):
        self.rulesets = {}
        with open(config_fp, 'r') as f:
            rulesets = yaml.safe_load(f)
        for rulename, ruleset in rulesets.items():
            if '_flatten' in ruleset:
                self.rulesets[rulename] = Flatten(ruleset['_flatten'])
            else:
                self.rulesets[rulename] = [
                    Mapping(keyto, fromdef)
                    for keyto, fromdef in ruleset.items()
                ]

    def parse(self, rulename: str, inputv: dict) -> dict | list:
        if rulename not in self.rulesets:
            raise Exception(f'no rulename {rulename} found')
        ruleset = self.rulesets.get(rulename)
        if isinstance(ruleset, list): # list of Mapping
            mapped = [
                rule.map(inputv)
                for rule in ruleset
            ]
            return {
                keyto : keyfrom
                for keyto, keyfrom in mapped
            }
        elif isinstance(ruleset, Flatten):
            return ruleset.flatten(inputv)

def handle_any(data_in: any, games_list: list, rulemap: RuleMap, datatype: str):
    for record in data_in:
        games_list.append(rulemap.parse(datatype, record))


def grab_all_json_files(indir: str, type: str):
    filepaths = []
    for path, _, files in os.walk(indir):
        for name in files:
            if fnmatch(name, f'{type}_*.json'):
                filepaths.append(Path(path, name))
    return filepaths

def main():
    parser = argparse.ArgumentParser("data transformer")
    parser.add_argument('-c', '--config', help='config file with mapping', required=True)
    parser.add_argument('-i', '--indir', help='json file input dir', required=True)
    parser.add_argument('-o', '--outdir', help='csv file output dir', required=True)
    parser.add_argument('-t', '--type', help='input value type', required=True)
    parser.add_argument('-interactive', help='do not save, break', default=False, action="store_true")

    args = parser.parse_args()
    rulemap = RuleMap(args.config)
    filepaths = grab_all_json_files(args.indir, 'playbyplays' if 'play' in args.type else args.type)
    for infile in filepaths:
        with open(infile, 'r') as f: 
            data_in = json.load(f)
        try:
            data_out = {}
            match args.type:
                case 'games':
                    data_out['games'] = []
                    handle_any(data_in, data_out['games'], rulemap, 'games')
                case 'plays':
                    data_out['plays'] = []
                    handle_any(data_in, data_out['plays'], rulemap, 'plays')
                case 'play_details':
                    data_out['play_details'] = []
                    handle_any(data_in, data_out['play_details'], rulemap, 'play_details')
                case 'rosters':
                    data_out['rosters'] = []
                    handle_any(data_in, data_out['rosters'], rulemap, 'rosters')
                case 'shifts':
                    data_out['shifts'] = []
                    handle_any(data_in, data_out['shifts'], rulemap, 'shifts')
                case _:
                    Logger.warning("nothing handled")
        except Exception as e:
            Logger.error(e)
        finally:
            for file, data in data_out.items():
                # data: to df
                data_out[file] = pl.DataFrame(data, infer_schema_length=None)
            if args.interactive:
                # file by file breakpoint
                breakpoint()
            else:
                for file, data in data_out.items():
                    # data: write out
                    poutfile = Path(args.outdir, f"{file}_{infile.with_suffix('.csv').name}")
                    data.write_csv(poutfile)
                    

if __name__ == "__main__":
    main()