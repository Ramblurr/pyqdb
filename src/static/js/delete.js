/* So this is redundant, it also exists in rating.js. I think it would be better
 * to create some kind of "namespace", if you will, using a javascript object and
 * have functions like this declared in there, so we can maximize code reuse. */
function quoteMessage(id, message)
{
    var css_id = "quote-live-vote-result-" + id;
    dojo.byId(css_id).innerHTML = message;
    dojo.fx.chain( [ dojo.fadeIn({node: css_id}), dojo.fadeOut({delay: 5000, node: css_id}) ]).play();
}

function QuoteDeleteRequest(resource, resultId, loadCallback, errorCallback) {
    this.resource = resource
    dojo.xhrDelete({
        url: resource,
        load: function (data) { loadCallback(resultId, data); },
        error: function (data) { errorCallback(resultId, data);}
    });
}

function remove_result(resultId, data) {
    if ( data == "success" ) {
        var css_id = "quote-" + resultId;
        dojo.fadeOut({
            delay: 100, 
            node: css_id,
            onEnd: function(){
                dojo.destroy(dojo.byId(css_id));
            }
        }).play();
    }
}

function remove_error(resultId, data) {
    quoteMessage(resultId, "Error Deleting");
}

function remove(e) {
    e.preventDefault();
    var resource = e.target.href;
    var id = e.target.id.split("-").pop();
    new QuoteDeleteRequest(resource, id, remove_result, remove_error);
}

dojo.ready(function() {
    dojo.query(".quote-remove").forEach(
        function(item, index, array) {
            dojo.connect(item, 'onclick', remove);
        }
    )
});
