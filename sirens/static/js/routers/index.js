Sirens.routers.Index = Backbone.Router.extend({
    views: {},
    current_content_view: null,

    initialize: function() {;
        return this;
    },

    start_routing: function() {
        Backbone.history.start();
    },

    get_or_create_view: function(name, options) {
        /*
         * Register each view as it is created and never create more than one.
         */
        if (name in this.views) {
            return this.views[name];
        }

        this.views[name] = new Sirens.views[name](options);

        return this.views[name];
    },

    routes: {
        "":                 "index"
    },

    index: function() {
        this.current_content_view = this.get_or_create_view("Index");
        this.current_content_view.reset();

        this.navigate("");
    },
});

