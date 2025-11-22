// AirTrafficSim.pde
import processing.data.JSONObject;
import processing.data.JSONArray;
import java.net.*;

JSONObject nodes;
JSONArray aircraft;

void setup() {
  size(600, 400);
}

void draw() {
  background(200);
  updateData();
  drawControllers();
  drawAircraft();
}

void updateData() {
  try {
    nodes = loadJSONObject("http://localhost:5000/nodes");
    aircraft = loadJSONArray("http://localhost:5000/aircraft");
  } catch (Exception e) {
    println("Backend not reachable");
  }
}

void drawControllers() {
  fill(150, 200, 255);
  rect(0, 0, width/2, height);   // Controller 1 zone
  rect(width/2, 0, width/2, height); // Controller 2 zone
}

void drawAircraft() {
  if (aircraft == null) return;
  for (int i = 0; i < aircraft.size(); i++) {
    JSONObject a = aircraft.getJSONObject(i);
    JSONArray pos = a.getJSONArray("pos");
    ellipse(pos.getInt(0), pos.getInt(1), 20, 20);
    text(a.getString("id"), pos.getInt(0)+10, pos.getInt(1));
  }
}
