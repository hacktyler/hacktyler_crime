Sirens.views.Index = Backbone.View.extend({
    active_calls: null,

    map: null,
    active_calls_features: null,

    pusher: null,
    channel: null,

    initialize: function() {
        _.bindAll(this, "render", "add_marker", "update_marker");

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
            center: center,
        });

        tiles = new L.TileLayer("http://{s}.google.com/vt/lyrs=m@155000000&hl=en&x={x}&y={y}&z={z}", {
            maxZoom: max_zoom,
            attribution: "Map data is Copyright Google, 2011",
            subdomains: ["mt0", "mt1", "mt2", "mt3"]
        });
        
        this.map.addLayer(tiles);

        this.active_calls_features = new L.LayerGroup();

        this.active_calls.each(this.add_marker);

        this.map.addLayer(this.active_calls_features);
    },

    init_socket: function() {
        this.pusher = new Pusher("d20fddb74c58823cd05d");
        this.channel = this.pusher.subscribe("active_calls");
        
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
        active_call.feature = new L.GeoJSON();

        active_call.feature.on("featureparse", function (e) {
            e.layer.bindPopup(e.properties.incident);
        });

        active_call.feature.addGeoJSON({ type: "Feature", geometry: active_call.get("point"), properties: active_call.toJSON() });

        this.active_calls_features.addLayer(active_call.feature); 

        ll = new L.LatLng(active_call.get("point").coordinates[1], active_call.get("point").coordinates[0]);
        this.map.setView(ll, 15);
    },

    update_marker: function(active_call) {
        this.active_calls_features.removeLayer(active_call.feature); 
        this.add_marker(active_call);
    }
});


