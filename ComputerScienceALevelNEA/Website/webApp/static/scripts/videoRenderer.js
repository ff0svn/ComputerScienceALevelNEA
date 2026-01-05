// https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API/Writing_WebSocket_client_applications

const init = Date.now() 

const wsURI = "http://172.22.24.151:10009"; // Figure out
const webSocket = new WebSocket(wsURI);
const firstMessage = true;

var width; var height; var fps; var time;
var update;

var canvas;
var canvasContext;

var frameBuffer = [];

webSocket.addEventListener("open", () => {
   console.log("Connected");

   webSocket.send(videoID);
   console.log("Data Sent");
});

webSocket.addEventListener("error", (event) => {
   console.log("ERROR: ", event);
   console.log(Date.now() - init);
});

webSocket.addEventListener("message", (e) => {
   console.log("recieved data: ${e.data}");

   if(firstMessage){
      firstMessage = false;

      const header = e.bytes();
      
      width = (header[0] << 8) + header[1];
      height = (header[2] << 8) + header[3];
      fps = header[4]; time = header[5];

      canvas = document.getElementById("canvas");
      canvasContext = canvas.getContext("2d");

      canvasContext.canvas.width = width;
      canvasContext.canvas.height = height;

      update = setInterval(function() {
         nextFrame();
      }, 1000 / fps);
   } else{
      var img = loadBlobAsImg(e);
      frameBuffer.push(img);
   }
});

webSocket.addEventListener("close", () => {
   console.log("Disconnected");
   
   clearInterval(update);
});

loadBlobAsDataUri = function(blob) {
  var fileReader = new FileReader();
  var future = fileReader.onLoad.first.then((event) => {
    return fileReader.result;
  });

  fileReader.readAsDataUrl(blob);
  return future;
}

loadBlobAsImg = function(blob) {
  var image = new ImageElement();
  return loadBlobAsDataUri(blob).then((dataUri) => {
    var loaded = image.onLoad.first;
    image.src = dataUri;
    return loaded.then((_) => image);
  });
}


nextFrame = function() {
   // Check there is an available frame to display
   // If not wait until next tick before trying again
   if(frameBuffer.length != 0){
      var frame = frameBuffer.shift(); // Acts as dequeue()

      canvasContext.putImageData(frame, 0, 0); // Push next frame to 
   }
}