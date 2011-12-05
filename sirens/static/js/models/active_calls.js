Sirens.models.ActiveCall = Backbone.Model.extend({
    urlRoot: Sirens.API + "/active_call"
});

Sirens.collections.ActiveCalls = Backbone.Collection.extend({
    model: Sirens.models.ActiveCall,
    url: Sirens.API + "/active_call"
});


