cloudgraph
==========

Cloudgraph is a minimal interface between Cloudwatch and Carbon/Graphite.
Requires boto.

### Usage

    from cloudgraph import CloudGraph
    with CloudGraph(method="pickle",
                    namespace="default") as cg:
                    
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(minutes=5)
    
        cg.get_metrics("HTTPStatus", dimension="foo", alt_dimension="bar") 
        cg.query_metrics(start, end, "Average", unit="Seconds")
        cg.send_pickle()
        


