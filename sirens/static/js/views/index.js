Sirens.views.Index = Backbone.View.extend({
    active_calls: null,

    map: null,
    active_calls_layers: null,
    popover_template: null,
    selected_layer: null,

    pusher: null,
    channel: null,
    member_count: 0,

    initialize: function() {
        _.bindAll(this, "render", "show_popover", "pan_to", "add_marker", "update_marker");

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
        
        this.map = new L.Map('map', {
            center:  new L.LatLng(lat, lng),
            zoom: zoom
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
        // Don't attempt to display if there is no location data
        if (active_call.get("point") == null) {
            return;
        }
                
        active_call.layer = new L.GeoJSON(null, {
            pointToLayer: _.bind(function (latlng) {
                return new L.CircleMarker(latlng);
            }, this)
        });

        active_call.layer.on("featureparse", _.bind(function(e) {
            e.layer.setStyle({
                radius: 6,
                color: "#000",
                weight: 1,
                opacity: 1,
                fillColor: "#ff7800",
                fillOpacity: 0.8
            });
            
            ll = new L.LatLng(e.properties.point.coordinates[1], e.properties.point.coordinates[0]);

            this.map.setView(ll, 15);
            this.show_popover(e.layer, e.properties);

            (function(layer, properties, mouseover_handler, click_handler) {
                layer.on("mouseover", function (e) { 
                    mouseover_handler(layer, properties);
                });

                layer.on("click", function(e) {
                    click_handler(properties);
                });
            })(e.layer, e.properties, this.show_popover, this.pan_to);
        }, this));

        active_call.layer.addGeoJSON({ type: "Feature", geometry: active_call.get("point"), properties: active_call.toJSON() });

        this.active_calls_layers.addLayer(active_call.layer); 
    },

    show_popover: function(layer, properties) {
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
        
        // Highlight only the selected point
        if (this.selected_layer) {
            this.selected_layer.setStyle({ fillColor: "#ff7800" });
        }

        layer.setStyle({ fillColor: "#ff0000" });
        this.selected_layer = layer;
    },

    pan_to: function(properties) {
        ll = new L.LatLng(properties.point.coordinates[1], properties.point.coordinates[0]);

        this.map.setView(ll, 15);
        this.show_popover(properties);
    },

    update_marker: function(active_call) {
        this.active_calls_layers.removeLayer(active_call.layer); 
        this.add_marker(active_call);
    },

    update_member_count: function() {
        $("#member-count").text(this.member_count);
    }
});


