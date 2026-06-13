const map = L.map('map').setView([43.2389, 76.8897], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

let start = null;
let end = null;
let routeLine = null;


//// load bus routes
//function getColor(id) {
//    // deterministic color from string
//    let hash = 0;
//    for (let i = 0; i < id.length; i++) {
//        hash = id.charCodeAt(i) + ((hash << 5) - hash);
//    }
//
//    const h = hash % 360;
//    return `hsl(${h}, 70%, 50%)`;
//}
//
//fetch("/routes/all")
//.then(r => r.json())
//.then(routes => {
//
//    routes.forEach(route => {
//
//        const color = getColor(route.routeId);
//
//        route.directions.forEach(direction => {
//
//            L.polyline(direction.line, {
//                color: color,
//                weight: 3,
//                opacity: 0.8
//            }).addTo(map);
//
//        });
//
//    });
//
//});

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

                if (start === null) {
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
        console.log("Direct buses:");

        data.buses.forEach(bus => {
            console.log(bus);
        });

     //   console.log("Possible busses:");
      //  data.buses.forEach(bus => {
       //     console.log(bus);
       // });
    });
}