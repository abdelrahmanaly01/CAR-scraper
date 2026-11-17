"""Isolated candidate lookup worker: reports progress over JSON lines."""
import argparse
import json
from .candidate_search import search_candidates


def emit(event, **data):
    print(json.dumps({'event':event, **data}), flush=True)

if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lat',type=float,required=True)
    parser.add_argument('--lon',type=float,required=True)
    args=parser.parse_args()
    try:
        result=search_candidates(args.lat,args.lon,lambda i,n:emit('candidate_progress',current=i,total=n))
        emit('candidates',**result)
    except Exception as exc:
        emit('error',message=str(exc))
