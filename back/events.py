import apis.kudago_place as kp
import apis.kudago_event as ke
import config
from rankers import rank_by_tags


def get_results_by_query(query):
    use_events = 'events' in query.search
    use_places = 'places' in query.search
    result = []

    if use_events:
        result.extend(ke.get_kudago_events_by_query(query))
    if use_places:
        result.extend(kp.get_kudago_places_by_query(query))
    if len(query.tags) == 0:
        ranks = range(len(result))
    else:
        print query.tags
        ranks = rank_by_tags(result, query)

    final_result = []
    for r in ranks[:config.show_result_num]:
        final_result.append(result[r])
    return final_result
