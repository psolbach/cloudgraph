cloudgraph
==========

Cloudgraph is a minimal interface for CloudWatch and Carbon/Graphite. Requires boto.  
The approach of chaining, manipulating metrics prior to submitting is chosen over piping output directly to `netcat`. Set intervals in your script and have Upstart or equivalent look out for it.

### Usage

    import cloudgraph
    with CloudGraph(method="pickle",
                    namespace="default") as cg:
                    
        end = datetime.datetime.utcnow()
        start = end - datetime.timedelta(minutes=5)
    
        cg.get_metrics("HTTPStatus", dimension="foo", alt_dimension="bar") 
        cg.query_metrics(start, end, "Average", unit="Seconds")
        
Optionally, manipulate stored data in cg.response. Then:
        
    cg.send_pickle()
        


