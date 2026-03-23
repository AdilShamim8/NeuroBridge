import { NeuroBridge, Profile } from "../src/index";

const bridge = new NeuroBridge({ debug: true });
bridge.setProfile(Profile.ANXIETY);

const response = bridge.adaptSync(
  "This is urgent and must be completed immediately. The risk increased by 38%."
);

console.log(response.adaptedText);
