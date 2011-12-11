Sirens.views.Index = Backbone.View.extend({
    active_calls: null,

    map: null,
    active_calls_layers: null,
    popover_template: null,
    active_call_item_template: null,
    selected_feature: null,

    pusher: null,
    channel: null,
    member_count: 0,

    initialize: function() {
        _.bindAll(this, "render", "show_popover", "pan_to", "add_marker", "update_marker");

        this.marker_template = _.template($("#marker-popover-template").html());
        this.active_call_item_template = _.template($("#active-call-item-template").html());

        this.init_active_calls();
        this.init_map();
        this.init_socket();

        $(".location").click({ view: this }, this.goto_location);

        $(".active-call-item").live("click", { view: this }, this.clicked_active_call_item);

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
        this.pusher = new Pusher(Sirens.settings.PUSHER_KEY);
        this.channel = this.pusher.subscribe(Sirens.settings.PUSHER_CHANNEL);

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
                weight: 1.5,
                opacity: 1,
                fillColor: "#f89406",
                fillOpacity: 1
            });

            (function(feature, active_call, mouseover_handler, click_handler) {
                feature.on("mouseover", function (e) { 
                    mouseover_handler(active_call);
                });

                feature.on("click", function(e) {
                    click_handler(active_call);
                });
            })(e.layer, active_call, this.show_popover, this.pan_to);
        }, this));

        active_call.layer.addGeoJSON({ type: "Feature", geometry: active_call.get("point"), properties: active_call.toJSON() });

        active_call.feature = this.feature_from_geojson(active_call.layer);

        this.active_calls_layers.addLayer(active_call.layer); 
        
        this.pan_to(active_call);
        this.refresh_active_calls_list();
    },

    feature_from_geojson: function(geojson) {
        /*
         * This is a super-dirty hack to work around Leaflet's lack of access
         * to individual geojson features. This only works because I know there
         * is only ever one feature in this data.
         */
        features = geojson._layers;

        for (var feature in features) {
            return features[feature];
        }
    },

    show_popover: function(active_call) {
        // Clear previous popover
        $("#marker-popover").remove();
        
        var popup = $("<div>", {
            "id": "marker-popover",
            "class": "popover"
        });

        var inner = $("<div>", {
            "class": "inner"
        }).appendTo(popup);

        var header = $("<div>", {
            "html": "<h4>" + active_call.get("incident") + "</h4>",
            "class": "title"
        }).appendTo(inner);

        var body = $("<div>", {
            "html": $(this.marker_template(active_call.toJSON())),
            "class": "content"
        }).appendTo(inner);

        popup.appendTo("#map");
        
        // Highlight only the selected point
        if (this.selected_feature) {
            this.selected_feature.setStyle({ fillColor: "#f89406" });
        }

        active_call.feature.setStyle({ fillColor: "#ff0000" });
        this.selected_feature = active_call.feature;    
    },

    pan_to: function(active_call) {
        ll = new L.LatLng(active_call.get("point").coordinates[1], active_call.get("point").coordinates[0]);

        this.map.setView(ll, 15, true);
        this.show_popover(active_call);
    },

    update_marker: function(active_call) {
        this.active_calls_layers.removeLayer(active_call.layer); 
        this.add_marker(active_call);
    },

    update_member_count: function() {
        $("#member-count").text(this.member_count);
    },

    refresh_active_calls_list: function() {
        $("#active-calls-list").empty();

        copy = this.active_calls.models.slice(0);
        copy.reverse(); 

        _.each(copy, _.bind(function(active_call) {
            $("#active-calls-list").append(this.active_call_item_template(active_call.toJSON()));
        }, this));
        
        $("#active-call-count").text(this.active_calls.length);
    },

    clicked_active_call_item: function(e) {
        active_call = e.data.view.active_calls.get($(this).attr("data-id"));

        e.data.view.pan_to(active_call); 
    },

    goto_location: function(e) {
        lat = $(this).attr("data-latitude");
        lng = $(this).attr("data-longitude");
        zoom = $(this).attr("data-zoom");

        console.log(lat, lng, zoom);

        e.data.view.map.setView(new L.LatLng(parseFloat(lat), parseFloat(lng)), zoom);

        return false;
    }
});


