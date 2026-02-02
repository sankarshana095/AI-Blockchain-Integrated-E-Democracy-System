setInterval(async () => {
    const res = await fetch("/evote/booth-status");
    const data = await res.json();
    if (data.active) {
        window.location.href = "/evote/vote";
    }
}, 3000);
