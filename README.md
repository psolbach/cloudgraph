cloudgraph
==========

Cloudgraph is a minimal interface between Carbon/Graphite and Cloudwatch.

### Usage

    with CloudGraph(method="pickle",
                    namespace="default") as cw:
                    
      while True:
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(minutes=5)
        
        cw.get_metrics("HTTPStatus", dimension="foo", alt_dimension="bar") 
        cw.query_metrics(start, end, "Average", unit="Seconds")
        cw.send_pickle()
        


