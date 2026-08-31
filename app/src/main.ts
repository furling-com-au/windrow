import { mount } from "svelte";
import App from "./App.svelte";
import "./mobile.css"; // touch-target floors, mobile breakpoint only (#30)

const app = mount(App, { target: document.getElementById("app")! });

export default app;
