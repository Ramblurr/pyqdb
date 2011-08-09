dojo.require("dijit.form.ComboBox");
dojo.require("dojox.form.MultiComboBox");
dojo.require("dojo.data.ItemFileReadStore");
dojo.require("dojo.string");

function TagGetRequest( resource, resultId, loadCallback, errorCallback )
{
    this.resource = resource;
    dojo.xhrGet({
        url: resource,
        handleAs: "json",
        headers: { "Accept": "application/vnd.pyqdb-tag+json" },
        load: function (data) { loadCallback(resultId, data); },
        error: function (data) { errorCallback(resultId, data); }
    });
}


function error_result(id, data)
{
    console.log("error: " + data);
}

function tag_cloud(id, tagData)
{
    var tc = TagCloud.create();
    for(var i = 0; i < tagData.length; ++i ) {
        tag = tagData[i].tag;
        count = tagData[i].count;
        tc.add(tag, count, '/tags/'+tag, 0);
    }
    tc.loadEffector('CountSize').base(24).range(15);
    tc.setup(id);
    return tc;
}

function setup_tagbox(id, tagStore)
{       
    var widget = new dojox.form.MultiComboBox({
        id: id,
        store: tagStore,
        searchAttr: "tag",
        name: "tags"
   }, id);
}

function setup_tagbox2(id, tagStore, changed)
{       
    var widget = new dijit.form.ComboBox({
        id: id,
        name: id,
        store: tagStore,
        searchAttr: "tag",
        onChange: changed
   }, id);
}

function fetch_result(id, data)
{
    if( data ) {
        var tagData = { identifier: 'tag', label: 'tag', items: data };
        var tagStore = new dojo.data.ItemFileReadStore( { data: tagData});
        tags_ready(data, tagStore);
    } else {
        error_result(id,data);
    }
}

dojo.ready(function(){
    var resource = "/tags";
    var id = "tag-cloud";
    new TagGetRequest(resource, id, fetch_result, error_result);
});

