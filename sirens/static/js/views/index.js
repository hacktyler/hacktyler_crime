Sirens.views.Index = Backbone.View.extend({
    active_calls: null,
    map: null,

    initialize: function() {
        // Create objects from bootstrap data
        this.active_calls = new Sirens.collections.ActiveCalls(Sirens.bootstrap.active_calls)
    },

    reset: function() {
        lat = 32.349549;
        lng = -95.301829;
        zoom = 14;
        
        var center = new L.LatLng(lat, lng);

        if (this.map == null) {
            this.map = new L.Map('map', {
                zoom: zoom,
                center: center,
            });

            tiles = new L.TileLayer("http://mt1.google.com/vt/lyrs=m@155000000&hl=en&x={x}&y={y}&z={z}&s={s}", {
                maxZoom: 17,
                attribution: "Map data is Copyright Google, 2011"
            });
            
            this.map.addLayer(tiles);

            geojson = new L.GeoJSON();

            geojson.on("featureparse", function (e) {
                e.layer.bindPopup(e.properties.incident);
            });

            this.active_calls.each(function(c) {
                geojson.addGeoJSON({ type: "Feature", geometry: c.get("point"), properties: c.toJSON() });
            });

            this.map.addLayer(geojson);
        }

        this.map.panTo(center);
    }
});


