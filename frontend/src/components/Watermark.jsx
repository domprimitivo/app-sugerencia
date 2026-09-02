// Marca de agua: composición de las dos épocas constructivas (arco de ladrillo
// moderno + ruinas romanas) con cielo, muy clara y degradada, para dar vida.
const WM_URL =
  'https://static.prod-images.emergentagent.com/jobs/e7139254-90e5-4523-b4d9-b1cffb260a97/images/64967349a105b898ab85facb571fcc2d4794088a936f6f8d64ca71a3fe6dbd29.jpeg';

export const Watermark = ({ opacity = 0.16 }) => (
  <div
    aria-hidden="true"
    data-testid="watermark"
    style={{
      position: 'fixed',
      inset: 0,
      zIndex: 0,
      pointerEvents: 'none',
      backgroundImage: `url(${WM_URL})`,
      backgroundSize: 'min(1100px, 88%)',
      backgroundPosition: 'center 60%',
      backgroundRepeat: 'no-repeat',
      opacity,
      WebkitMaskImage: 'radial-gradient(ellipse at center, black 50%, transparent 86%)',
      maskImage: 'radial-gradient(ellipse at center, black 50%, transparent 86%)',
    }}
  />
);

export default Watermark;
