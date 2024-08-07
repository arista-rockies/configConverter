# configConverter

Utilizes several tools to convert switch configurations to Arista EOS
- Arista AVD (https://avd.sh/en/stable/)
- The amazing config parser library from (https://github.com/tdorssers/confparser.git) included here with a single modification to output an alert for non-matching lines

## Requirements
`pip install -r requirements.txt`

## usage
```
$ python configConverter.py --help
usage: configConverter.py [-h] -i I [--dissector DISSECTOR]

options:
  -h, --help            show this help message and exit
  -i I                  input file
  --dissector DISSECTOR
                        dissector file. default=ios.yaml
```
