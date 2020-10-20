import pysolr
from ckan.plugins.toolkit import get_or_bust, side_effect_free
from ckan.logic import ActionError
from ckan.lib.search.common import make_connection
import ckan.plugins.toolkit as tk

import logging
log = logging.getLogger(__name__)


@side_effect_free
def ogdzh_autosuggest(context, data_dict):
    """
    collecting autosuggestions from solr by calling
    :param q: the search term
           example: velo
    :param cfq: a context as facet-names concatenated by AND
           example: 'soziales AND bevolkerung'
    :return: autosuggestions that were generated by solr
             by the suggest handler
             as a list of unique suggestions
    """
    q = get_or_bust(data_dict, 'q')
    cfq = data_dict.get('cfq', '')

    if cfq:
        cfq = 'active AND %s' % cfq
    else:
        cfq = 'active'
    handler = '/suggest'
    suggester = 'default'
    suggest_search_limit = int(tk.config.get(
        'ckanext.stadtzh-theme.ogdzh_autosuggest_search_limit', 100))
    suggest_results_limit = int(tk.config.get(
        'ckanext.stadtzh-theme.ogdzh_autosuggest_result_limit', 10))

    log.debug(
        'Loading suggestions for {} (cfq: {}) with handler {}, '
        'suggester {}, result-limit {}, search-limit {}'
        .format(
            q, cfq, handler, suggester, suggest_results_limit,
            suggest_search_limit
        ))

    try:
        solr = make_connection()
        results = solr.search(
            '',
            search_handler=handler,
            **{'suggest.q': q,
               'suggest.count': suggest_search_limit,
               'suggest.cfq': cfq}
        )
        suggestions = results.raw_response['suggest'][suggester].values()[0]
        log.debug("suggestions found: {}".format(suggestions))
        terms = \
            list(set([suggestion['term']
                      for suggestion
                      in suggestions['suggestions']]))[:suggest_results_limit]
        log.debug("suggestions found: {}".format(terms))
        return list(set(terms))
    except pysolr.SolrError as e:
        log.exception('Could not load suggestions from solr: %s' % e)
        raise ActionError('Error retrieving suggestions from solr')
