dojo.require("dojo.NodeList-traverse");
dojo.require("dojo.fx");

function quoteMessage(id, message)
{
    var css_id = "quote-live-vote-result-" + id;
    dojo.byId(css_id).innerHTML = message;
    dojo.fx.chain( [ dojo.fadeIn({node: css_id}), dojo.fadeOut({delay: 5000, node: css_id}) ]).play();
}

function QuotePutRequest( resource, data, resultId, loadCallback, errorCallback )
{
    this.resource = resource;
    this.data = data;
    dojo.xhrPut({
        url: resource,
        putData: data,
        handleAs: "json",
        load: function (data) { loadCallback(resultId, data); },
        error: function (data) { errorCallback(resultId, data); }
    });
}

function vote_result(id, data)
{
    if( data ) {
        dojo.byId("quote-rating-" + data.id).innerHTML = data.up - data.down;
        dojo.byId("quote-vote-count-" + data.id).innerHTML = data.up + data.down;
        quoteMessage(id, "Vote Counted");
    } else {
        quoteMessage(id, "Already Voted");
    }
}

function error_result(id, data)
{
    quoteMessage(id, "Error");
}

function rate(e, type)
{
    e.preventDefault();
    var resource = e.target.href;
    var id = e.target.id.split("-").pop();
    new QuotePutRequest(resource, "type="+type, id, vote_result, error_result);
    dojo.addClass(e.target, "casted-vote");
    return false;
}

function rate_up(e)
{
    rate(e, "up");
}

function rate_down(e)
{
    rate(e, "down");
}

function nyi(e)
{
    e.preventDefault();
    var id = e.target.id.split("-").pop();
    quoteMessage(id, "Not Yet Implemented");
    return false;
}

dojo.ready(function(){
    dojo.query("a.quote-rating-up").forEach(
        function(item, index, array) {
            dojo.connect(item, 'onclick', rate_up);
        }
    );
    dojo.query("a.quote-rating-down").forEach(
        function(item, index, array) {
            dojo.connect(item, 'onclick', rate_down);
        }
    );
    dojo.query("a.quote-report").forEach(
        function(item, index, array) {
            dojo.connect(item, 'onclick', nyi);
        }
    );

});