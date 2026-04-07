let scene, camera, renderer, magnifyingGlass;

function initThreeJS() {
    const container = document.getElementById('loading-overlay');
    container.innerHTML = ''; // Clear previous
    
    scene = new THREE.Scene();
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    
    renderer = new THREE.WebGLRenderer({ alpha: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    container.appendChild(renderer.domElement);

    // Create Magnifying Glass (Simplified 3D shapes)
    const group = new THREE.Group();
    
    // The Ring
    const ringGeom = new THREE.TorusGeometry(1, 0.1, 16, 100);
    const material = new THREE.MeshBasicMaterial({ color: 0x000000 });
    const ring = new THREE.Mesh(ringGeom, material);
    group.add(ring);

    // The Lens (Fisheye effect simulated by SphereGeometry)
    const lensGeom = new THREE.SphereGeometry(0.95, 32, 32, 0, Math.PI * 2, 0, 0.5);
    const lensMat = new THREE.MeshPhongMaterial({ 
        color: 0xffffff, 
        transparent: true, 
        opacity: 0.4, 
        shininess: 100 
    });
    const lens = new THREE.Mesh(lensGeom, lensMat);
    lens.rotation.x = Math.PI / 2;
    group.add(lens);

    // The Handle
    const handleGeom = new THREE.CylinderGeometry(0.1, 0.1, 1.5);
    const handle = new THREE.Mesh(handleGeom, material);
    handle.position.y = -1.8;
    group.add(handle);

    scene.add(group);
    camera.position.z = 5;

    const light = new THREE.PointLight(0xffffff, 1, 100);
    light.position.set(5, 5, 5);
    scene.add(light);

    function animate() {
        if(container.style.display === 'none') return;
        requestAnimationFrame(animate);
        group.rotation.z += 0.05; // Clockwise float
        group.rotation.y += 0.02; // Slight 3D wobble
        renderer.render(scene, camera);
    }
    animate();
}