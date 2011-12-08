Sirens.views.Index = Backbone.View.extend({
    active_calls: null,

    map: null,
    active_calls_layers: null,
    popover_template: null,

    marker_style: {
        radius: 8,
        fillColor: "#ff7800",
        color: "#000",
        weight: 1,
        opacity: 1,
        fillOpacity: 0.8
    },

    pusher: null,
    channel: null,
    member_count: 0,

    initialize: function() {
        _.bindAll(this, "render", "show_popover", "add_marker", "update_marker");

        this.marker_template = _.template($("#marker-popover-template").html());

        this.init_active_calls();
        this.init_map();
        this.init_socket();

        return this;
    },

    init_active_calls: function() {
        this.active_calls = new Sirens.collections.ActiveCalls(Sirens.bootstrap.active_calls)
    },

    init_map: function() {
        lat = 32.349549;
        lng = -95.301829;
        zoom = 12;
        max_zoom = 17;
        
        var center = new L.LatLng(lat, lng);

        this.map = new L.Map('map', {
            zoom: zoom,
        });

        tiles = new L.TileLayer("http://{s}.google.com/vt/lyrs=m@155000000&hl=en&x={x}&y={y}&z={z}", {
            maxZoom: max_zoom,
            attribution: "Map data is Copyright Google, 2011",
            subdomains: ["mt0", "mt1", "mt2", "mt3"]
        });
        
        this.map.addLayer(tiles);

        this.active_calls_layers = new L.LayerGroup();

        this.active_calls.each(this.add_marker);

        this.map.addLayer(this.active_calls_layers);
    },

    init_socket: function() {
        this.pusher = new Pusher("d20fddb74c58823cd05d");
        this.channel = this.pusher.subscribe("presence-active-calls");

        this.channel.bind("pusher:subscription_succeeded", _.bind(function(members) {
            this.member_count = members.count;
            this.update_member_count();
        }, this));
       
        this.channel.bind("pusher:member_added", _.bind(function(member) {
            this.member_count += 1;
            this.update_member_count();
        }, this));
        
        this.channel.bind("pusher:member_removed", _.bind(function(member) {
            this.member_count -= 1;
            this.update_member_count();
        }, this));

        this.channel.bind("new_active_call", _.bind(function(data) {
            active_call = new Sirens.models.ActiveCall(data);
            this.active_calls.add(active_call);
            this.add_marker(active_call);
        }, this));

        this.channel.bind("changed_active_call", _.bind(function(data) {
            var existing = this.active_calls.get(data.id);

            if (existing) {
                existing.set(data);
                this.update_marker(existing);
            } else {
                active_call = new Sirens.models.ActiveCall(data);
                this.active_calls.add(active_call);
                this.add_marker(active_call);
            }
        }, this));
    },

    add_marker: function(active_call) {
        active_call.layer = new L.GeoJSON(null, {
            pointToLayer: _.bind(function (latlng) {
                return new L.CircleMarker(latlng);
            }, this)
        });

        active_call.layer.on("featureparse", _.bind(function(e) {
            e.layer.setStyle(this.marker_style);

            (function(properties, mouseover_handler) {
                e.layer.on("mouseover", function (e) { 
                    mouseover_handler(properties);
                });
            })(e.properties, this.show_popover);
        }, this));

        active_call.layer.addGeoJSON({ type: "Feature", geometry: active_call.get("point"), properties: active_call.toJSON() });

        this.active_calls_layers.addLayer(active_call.layer); 

        ll = new L.LatLng(active_call.get("point").coordinates[1], active_call.get("point").coordinates[0]);

        this.map.setView(ll, 15);
        this.show_popover(active_call.toJSON());
    },

    show_popover: function(properties) {
        // Clear previous popover
        $("#marker-popover").remove();
        
        var popup = $("<div>", {
            id: "marker-popover",
            class: "popover",
            css: {
                top: "15px",
                right: "15px",
                left: "auto",
                display: "block"
            }
        });

        var inner = $("<div>", {
            class: "inner"
        }).appendTo(popup);

        var header = $("<div>", {
            html: "<h4>" + properties.incident + "</h4>",
            class: "title"
        }).appendTo(inner);

        var body = $("<div>", {
            html: $(this.marker_template(properties)),
            class: "content"
        }).appendTo(inner);

        popup.appendTo("#map");
    },

    update_marker: function(active_call) {
        this.active_calls_layers.removeLayer(active_call.layer); 
        this.add_marker(active_call);
    },

    update_member_count: function() {
        $("#member-count").text(this.member_count);
    }
});


