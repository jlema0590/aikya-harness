"""Cumulative limits over the existing durable result ledger, including Review."""


def remaining(config, ledger):
    result={'max_turns':config['max_turns'],'recorded_tokens_remaining':None,'reason':None}
    if config.get('max_total_turns') is not None:
        turns=[row.get('num_turns') for row in ledger['results'].values()]
        if any(type(value) is not int or value<0 for value in turns):
            result['reason']='turn_usage_unavailable';return result
        result['max_turns']=min(config['max_turns'],max(0,config['max_total_turns']-sum(turns)))
        if result['max_turns']==0:result['reason']='turn_limit'
    if config.get('max_recorded_tokens') is not None:
        if not ledger.get('tokens_known',False):
            result['reason']='token_usage_unavailable';return result
        result['recorded_tokens_remaining']=max(0,config['max_recorded_tokens']-sum(ledger['token_totals'].values()))
        if result['recorded_tokens_remaining']==0:result['reason']='token_limit'
    return result
