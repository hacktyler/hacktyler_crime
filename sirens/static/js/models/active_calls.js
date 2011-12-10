Sirens.models.ActiveCall = Backbone.Model.extend({
    urlRoot: Sirens.API + "/active_call"
});

Sirens.collections.ActiveCalls = Backbone.Collection.extend({
    model: Sirens.models.ActiveCall,
    url: Sirens.API + "/active_call",

    comparatorcollection: function(active_call) {
        return active_call.get("reported");
    }
});


