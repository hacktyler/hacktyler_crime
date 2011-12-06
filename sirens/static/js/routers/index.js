Sirens.routers.Index = Backbone.Router.extend({
    index_view: null,
    current_content_view: null,

    initialize: function() {;
        this.index_view = new Sirens.views.Index();

        return this;
    },

    start_routing: function() {
        Backbone.history.start();
    },

    routes: {
        "":                 "index"
    },

    index: function() {
        this.navigate("");
    },
});

