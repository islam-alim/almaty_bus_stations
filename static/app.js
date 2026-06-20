const map = L.map('map').setView([43.2389, 76.8897], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19
}).addTo(map);

let start = null;
let end = null;
let routeLine = null;
let routeSegments = [];
let routeLayerGroups = [];
let allStops = [];
const markersByStopId = new Map();
const routeColors = ["#0b63ce", "#d97706", "#7b3fc7"];
const routeBaseWeights = [9, 6, 3];

const routeForm = document.getElementById("route-form");
const startInput = document.getElementById("start-stop");
const endInput = document.getElementById("end-stop");
const stopOptions = document.getElementById("stop-options");
const routeStatus = document.getElementById("route-status");
const routeBuses = document.getElementById("route-buses");
const routeOptions = document.getElementById("route-options");


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
        allStops = stops.map(stop => ({
            ...stop,
            optionLabel: `${stop.name} (#${stop.id})`
        }));

        stopOptions.innerHTML = "";
        allStops.forEach(stop => {
            const option = document.createElement("option");
            option.value = stop.optionLabel;
            stopOptions.appendChild(option);
        });

        allStops.forEach(stop => {

            const marker = L.circleMarker([stop.lat, stop.lon], {
                radius: 5,
                color: "red",
                fillColor: "red",
                fillOpacity: 0.7
            }).addTo(map);

            marker.bindTooltip(stop.name);
            markersByStopId.set(stop.id, marker);

            marker.on("click", () => {
                setSelectedStop(stop);
            });
        });
    });

routeForm.addEventListener("submit", event => {
    event.preventDefault();
    setRouteFromInputs();
});

startInput.addEventListener("change", setRouteFromInputs);
endInput.addEventListener("change", setRouteFromInputs);

function setSelectedStop(stop) {
    routeStatus.textContent = "";

    if (start === null || (start !== null && end !== null)) {
        clearRoute();
        start = stop.id;
        end = null;
        startInput.value = stop.optionLabel;
        endInput.value = "";
        console.log("Start:", start);
        return;
    }

    end = stop.id;
    endInput.value = stop.optionLabel;
    console.log("End:", end);
    getRoute();
}

function setRouteFromInputs() {
    const selectedStart = findStopByInput(startInput.value);
    const selectedEnd = findStopByInput(endInput.value);

    routeStatus.textContent = "";

    if (startInput.value.trim() && !selectedStart) {
        routeStatus.textContent = "Start stop was not found.";
        return;
    }

    if (endInput.value.trim() && !selectedEnd) {
        routeStatus.textContent = "End stop was not found.";
        return;
    }

    start = selectedStart ? selectedStart.id : null;
    end = selectedEnd ? selectedEnd.id : null;

    if (start !== null) {
        startInput.value = selectedStart.optionLabel;
    }

    if (end !== null) {
        endInput.value = selectedEnd.optionLabel;
    }

    if (start !== null && end !== null) {
        getRoute();
    }
}

function findStopByInput(value) {
    const query = value.trim().toLowerCase();

    if (!query) {
        return null;
    }

    const idMatch = query.match(/\(#(\d+)\)$/);
    if (idMatch) {
        const stopId = Number(idMatch[1]);
        return allStops.find(stop => stop.id === stopId) || null;
    }

    return allStops.find(stop => stop.name.toLowerCase() === query)
        || allStops.find(stop => stop.name.toLowerCase().includes(query))
        || null;
}

function clearRoute() {
    if (routeLine) {
        map.removeLayer(routeLine);
        routeLine = null;
    }

    routeSegments.forEach(segment => map.removeLayer(segment));
    routeSegments = [];
    routeLayerGroups.forEach(layers => {
        layers.forEach(layer => {
            if (map.hasLayer(layer)) {
                map.removeLayer(layer);
            }
        });
    });
    routeLayerGroups = [];

    markersByStopId.forEach(marker => {
        marker.setStyle({
            color: "red",
            fillColor: "red",
            fillOpacity: 0.7
        });
    });

    routeBuses.textContent = "-";
    routeOptions.innerHTML = "";
}

function focusStop(stopId) {
    const marker = markersByStopId.get(stopId);

    if (marker) {
        marker.setStyle({
            color: "#0b63ce",
            fillColor: "#0b63ce",
            fillOpacity: 0.85
        });
    }
}

map.on("contextmenu", event => {
    let nearestStop = null;
    let nearestDistance = Infinity;

    allStops.forEach(stop => {
        const distance = event.latlng.distanceTo([stop.lat, stop.lon]);

        if (distance < nearestDistance) {
            nearestDistance = distance;
            nearestStop = stop;
        }
    });

    if (nearestStop) {
        setSelectedStop(nearestStop);
    }
});

function getRoute() {
    if (start === null || end === null) {
        return;
    }

    routeStatus.textContent = "";

    fetch("/route", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({start, end})
    })
    .then(res => res.json())
    .then(data => {

        const routes = data.routes && data.routes.length > 0
            ? data.routes.slice(0, 3)
            : [{
                route: data.route,
                instructions: data.instructions || [],
                buses: data.buses || []
            }];

        clearRoute();

        if (!routes[0].route || routes[0].route.length === 0) {
            console.warn("No route returned", data);
            routeStatus.textContent = "No route was found.";
            routeBuses.textContent = "-";
            return;
        }

        renderRouteAlternatives(routes);
        console.log("Route options:", routes);
        focusStop(start);
        focusStop(end);

     //   console.log("Possible busses:");
      //  data.buses.forEach(bus => {
       //     console.log(bus);
       // });
    })
    .catch(error => {
        console.error("Route error:", error);
        routeStatus.textContent = "Could not build the route.";
        routeBuses.textContent = "-";
    });
}

function renderRouteAlternatives(routes) {
    routes.forEach((route, routeIndex) => {
        routeLayerGroups[routeIndex] = drawRoute(route, routeIndex);

        const option = document.createElement("button");
        option.type = "button";
        option.className = "route-option";
        option.innerHTML = `
            <span class="route-swatch" style="background:${routeColors[routeIndex % routeColors.length]}"></span>
            <span>Route ${routeIndex + 1}: ${transferText(route)}, ${busesText(route)}</span>
        `;
        option.addEventListener("click", () => setActiveRoute(routeIndex, routes));
        routeOptions.appendChild(option);
    });

    setActiveRoute(0, routes);

    if (routeSegments.length > 0) {
        const group = L.featureGroup(routeSegments);
        map.fitBounds(group.getBounds());
    }
}

function drawRoute(route, routeIndex) {
    const latlngs = route.route;
    const instructions = route.instructions || [];
    const color = routeColors[routeIndex % routeColors.length];
    const busWeight = routeBaseWeights[routeIndex] || 4;
    const walkWeight = Math.max(2, busWeight - 3);
    const layers = [];

    if (instructions.length === latlngs.length - 1) {
        for (let i = 0; i < instructions.length; i++) {
            const instruction = instructions[i];
            const isBus = instruction.mode === "bus";

            const segment = L.polyline([latlngs[i], latlngs[i + 1]], {
                color,
                weight: isBus ? busWeight : walkWeight,
                opacity: 0.86,
                dashArray: isBus ? null : "6 8"
            }).addTo(map);

            segment.routeIsBus = isBus;

            if (isBus && instruction.route) {
                segment.bindTooltip(`Route ${routeIndex + 1}, bus ${instruction.route}`);
            }

            layers.push(segment);
            routeSegments.push(segment);
        }

        for (let i = 1; i < instructions.length; i++) {
            const previous = instructions[i - 1];
            const next = instructions[i];
            const transferKind = transferPointKind(instructions, i);

            if (!transferKind) {
                continue;
            }

            const marker = createTransferMarker(latlngs[i], transferKind, previous, next, routeIndex);
            marker.addTo(map);
            layers.push(marker);
        }
    }
    else {
        const segment = L.polyline(latlngs, {
            color,
            weight: busWeight,
            opacity: 0.86
        }).addTo(map);

        segment.routeIsBus = true;
        layers.push(segment);
        routeSegments.push(segment);
    }

    return layers;
}

function transferPointKind(instructions, index) {
    const previous = instructions[index - 1];
    const next = instructions[index];

    if (!previous || !next) {
        return null;
    }

    const previousIsBus = previous.mode === "bus";
    const nextIsBus = next.mode === "bus";

    if (previousIsBus && nextIsBus && previous.route !== next.route) {
        return "bus-transfer";
    }

    if (
        previous.mode === "bus"
        && next.mode === "walk"
        && isWalkingConnectionBetweenBusSegments(instructions, index)
    ) {
        return "walking-transfer";
    }

    return null;
}

function isWalkingConnectionBetweenBusSegments(instructions, index) {
    const previousBus = findNearestBusInstruction(instructions, index - 1, -1);
    const nextBus = findNearestBusInstruction(instructions, index, 1);

    return Boolean(previousBus && nextBus && previousBus.route !== nextBus.route);
}

function findNearestBusInstruction(instructions, startIndex, step) {
    for (let i = startIndex; i >= 0 && i < instructions.length; i += step) {
        const instruction = instructions[i];

        if (instruction.mode === "bus" && instruction.route) {
            return instruction;
        }
    }

    return null;
}

function createTransferMarker(latlng, kind, previous, next, routeIndex) {
    const isBusTransfer = kind === "bus-transfer";
    const label = isBusTransfer ? "Bus transfer" : "Walking connection";
    const detail = `${label}: ${instructionLabel(previous)} to ${instructionLabel(next)}`;

    return L.marker(latlng, {
        interactive: true,
        icon: L.divIcon({
            className: "",
            html: `
                <span class="transfer-marker ${kind}" style="--route-color:${routeColors[routeIndex % routeColors.length]}">
                    <span class="transfer-symbol"></span>
                </span>
            `,
            iconSize: [28, 28],
            iconAnchor: [14, 14]
        })
    }).bindTooltip(detail);
}

function instructionLabel(instruction) {
    if (instruction.mode === "bus" && instruction.route) {
        return `bus ${instruction.route}`;
    }

    return "walk";
}

function setActiveRoute(activeIndex, routes) {
    const options = routeOptions.querySelectorAll(".route-option");

    routeLayerGroups.forEach((layers, routeIndex) => {
        const isActive = routeIndex === activeIndex;
        const busWeight = routeBaseWeights[routeIndex] || 4;
        const walkWeight = Math.max(2, busWeight - 3);

        layers.forEach(layer => {
            const opacity = isActive ? 0.96 : 0.72;

            if (layer.setStyle) {
                layer.setStyle({
                    opacity,
                    weight: layer.routeIsBus
                        ? (isActive ? busWeight + 2 : busWeight)
                        : (isActive ? walkWeight + 2 : walkWeight)
                });
            }

            if (layer.setOpacity) {
                layer.setOpacity(isActive ? 1 : 0.58);
            }
        });
    });

    options.forEach((option, optionIndex) => {
        option.classList.toggle("active", optionIndex === activeIndex);
    });

    routeBuses.textContent = busesText(routes[activeIndex]);
}

function busesText(route) {
    const buses = route.buses && route.buses.length > 0
        ? route.buses
        : [...new Set(
            (route.instructions || [])
                .filter(instruction => instruction.mode === "bus" && instruction.route)
                .map(instruction => instruction.route)
        )];

    return buses.length > 0 ? buses.join(", ") : "No bus needed";
}

function transferText(route) {
    const transfers = route.transfers || 0;

    return transfers === 1 ? "1 transfer" : `${transfers} transfers`;
}
