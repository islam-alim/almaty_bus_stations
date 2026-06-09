const map = L.map('map').setView([43.2389, 76.8897], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

let start = null;
let end = null;
let routeLine = null;

// load stops
fetch("/stops")
    .then(res => res.json())
    .then(stops => {

        stops.forEach(stop => {

            const marker = L.circleMarker([stop.lat, stop.lon], {
                radius: 5,
                color: "red"
            }).addTo(map);

            marker.on("click", () => {

                if (!start) {
                    start = stop.id;
                    console.log("Start:", start);
                }
                else {
                    end = stop.id;
                    console.log("End:", end);
                    getRoute();
                }
            });
        });
    });


function getRoute() {

    fetch("/route", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({start, end})
    })
    .then(res => res.json())
    .then(data => {

        const latlngs = data.route;

        if (routeLine) {
            map.removeLayer(routeLine);
        }

        routeLine = L.polyline(latlngs, {color: "blue"}).addTo(map);

        map.fitBounds(routeLine.getBounds());
    });
}