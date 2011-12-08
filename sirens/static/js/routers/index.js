Sirens.routers.Index = Backbone.Router.extend({
    index_view: null,

    initialize: function() {;
        this.index_view = new Sirens.views.Index();

        $(".modal-close").live("click", function() {
            $(this).parents(".modal").modal("hide");
        });

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

