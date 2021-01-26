map = (function () {
  "use strict";

  var analysing = false;
  var done = false;
  var tempCanvas;
  var spread = 1;
  var widening = false;
  var moving = false;
  var analysing = false;
  var done = false;
  var scene_loaded = false;
  var lastumax = null;
  var u_max = 8848;
  var u_min = 0;
  var diff = null;

  var slider = document.getElementById("myRange");

  var map = L.map("mapid").setView([51.505, -0.09], 13);

  var layer = Tangram.leafletLayer({
    scene: "scene.yaml",
    attribution:
      '<a href="https://mapzen.com/tangram" target="_blank">Tangram</a> | &copy; OSM contributors',
    postUpdate: function () {
      // three stages:
      // 1) start analysis
      if (!analysing && !done) {
        expose();
      }
      // 2) continue analysis
      else if (analysing && !done) {
        start_analysis();
      }
      // 3) stop analysis and reset
      else if (done) {
        done = false;
      }
    },
  });

  layer.addTo(map);

  var circle = L.circle()
    .setRadius(slider.value)
    .setLatLng([51.5, -0.09])
    .addTo(map);

  function onMapClick(e) {
    circle.setLatLng(e.latlng);
  }
  function onSliderChange(e) {
    circle.setRadius(e.latlng);
  }
  slider.oninput = function () {
    circle.setRadius(this.value);
  };
  map.on("click", onMapClick);

  function expose() {
    analysing = true;
    if (scene_loaded) {
      start_analysis();
    } else {
      // wait for scene to initialize first
      scene.initializing.then(function () {
        start_analysis();
      });
    }
  }

  function start_analysis() {
    // set levels
    var levels = analyse();
    diff = levels.max - lastumax;
    if (typeof levels.max !== "undefined") lastumax = levels.max;
    else diff = 1;
    // was the last change a widening or narrowing?
    widening = diff < 0 ? false : true;
    if (levels) {
      scene.styles.combo.shaders.uniforms.u_min = levels.min;
      scene.styles.combo.shaders.uniforms.u_max = levels.max;
    }
    scene.requestRedraw();
  }

  function analyse() {
    var ctx = tempCanvas.getContext("2d"); // Get canvas 2d context
    ctx.clearRect(0, 0, tempCanvas.width, tempCanvas.height);

    // redraw canvas smaller in testing canvas, for speed
    ctx.drawImage(scene.canvas, 0, 0, scene.canvas.width, scene.canvas.height);
    // get all the pixels
    var pixels = ctx.getImageData(0, 0, tempCanvas.width, tempCanvas.height);
    var val;
    var counts = {};
    var empty = true;
    var max = 0,
      min = 255;
    // only check every nth pixel (vary with browser size)
    // var stride = Math.round(img.height * img.width / 1000000);
    // 4 = only sample the red value in [R, G, B, A]
    for (var i = 0; i < tempCanvas.height * tempCanvas.width * 4; i += 4) {
      val = pixels.data[i];
      var alpha = pixels.data[i + 3];
      if (alpha === 0) {
        // empty pixel, skip to the next one
        continue;
      }
      // if we got this far, we found at least one non-empty pixel!
      empty = false;
      // update counts, to get a histogram
      counts[val] = counts[val] ? counts[val] + 1 : 1;

      // update min and max so far
      min = Math.min(min, val);
      max = Math.max(max, val);
    }

    if (empty) {
      // no pixels found, skip the analysis
      return false;
    }
    if (max > 253 && min < 4 && !widening) {
      // looks good, done
      analysing = false;
      done = true;
      spread = 2;
      return false;
    }
    if (max > 252 && min < 4 && widening) {
      // over-exposed, widen the range
      spread *= 2;
      // cap spread
      spread = Math.min(spread, 512);
      // console.log("WIDEN >", spread, "   diff:", diff)
      max += spread;
      min -= spread;
    }

    // calculate adjusted elevation settings based on current pixel
    // values and elevation settings
    var range = u_max - u_min;
    var minadj = (min / 255) * range + u_min;
    var maxadj = (max / 255) * range + u_min;

    // keep levels in range
    minadj = Math.max(minadj, -11000);
    maxadj = Math.min(maxadj, 8900);
    // only let the minimum value go below 0 if ocean data is included
    minadj = Math.max(minadj, 0);

    // keep min and max separated
    if (minadj === maxadj) maxadj += 10;

    // get the width of the current view in meters
    // compare to the current elevation range in meters
    // the ratio is the "height" of the current scene compared to its width –
    // multiply it by the width of your 3D mesh to get the height
    var zrange = u_max - u_min;
    var xscale = zrange / scene.view.size.meters.x;

    scene.styles.combo.shaders.uniforms.u_min = minadj;
    scene.styles.combo.shaders.uniforms.u_max = maxadj;

    // update dat.gui controllers
    u_min = minadj;
    u_max = maxadj;

    updateLabels(minadj, maxadj);
    return { max: maxadj, min: minadj };
  }

  function updateLabels(min, max) {
    document.getElementById("minlabel").innerHTML = "min: " + min;
    document.getElementById("maxlabel").innerHTML = "max: " + max;
  }
  // from https://davidwalsh.name/javascript-debounce-function
  function debounce(func, wait, immediate) {
    var timeout;
    return function () {
      var context = this,
        args = arguments;
      var later = function () {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  }

  window.layer = layer;
  var scene = layer.scene;
  window.scene = scene;

  /***** Render loop *****/
  window.addEventListener("load", function () {
    // Scene initialized
    layer.on("init", function () {
      // resetViewComplete();
      scene.subscribe({
        // will be triggered when tiles are finished loading
        // and also manually by the moveend event
        view_complete: function () {},
      });
      scene_loaded = true;
      tempCanvas = document.createElement("canvas");

      // document.body.appendChild(tempCanvas);
      // tempCanvas.style.position = "absolute";
      // tempCanvas.style.zIndex = 10000;
      tempCanvas.width = scene.canvas.width / tempFactor;
      tempCanvas.height = scene.canvas.height / tempFactor;
    });
    layer.addTo(map);

    // debounce moveend event
    var moveend = debounce(function (e) {
      moving = false;
      // manually reset view_complete
      scene.resetViewComplete();
      scene.requestRedraw();
    }, 250);

    map.on("movestart", function (e) {
      moving = true;
    });
    map.on("moveend", function (e) {
      moveend(e);
    });

    // toggleNew(true);
  });
})();
