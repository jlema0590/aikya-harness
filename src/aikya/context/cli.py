"""Read bounded context without a model call."""
import argparse
import json
from pathlib import Path
from .prepare import prepare_context


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target',type=Path,default=Path.cwd())
    parser.add_argument('--query',default='')
    parser.add_argument('--allowed-file',action='append',default=None)
    parser.add_argument('--max-chars',type=int,default=6000)
    args=parser.parse_args(argv)
    try:
        print(json.dumps(prepare_context(args.target,args.query,paths=args.allowed_file,max_chars=args.max_chars),ensure_ascii=False))
        return 0
    except (ValueError,OSError) as exc:
        parser.exit(2,str(exc)+'\n')
