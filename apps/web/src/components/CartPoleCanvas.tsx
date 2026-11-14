import { useEffect, useRef } from 'react';
import { poleTip } from '#/lib/cartpole';

/** Canvas CartPole renderer. React never renders per-frame: the parent
 * owns the timestep state and this component draws the current
 * observation [x, xDot, theta, thetaDot] on each change via useEffect.
 * Falls back gracefully when canvas 2d is unavailable (jsdom). */

const TRACK_HALF = 2.4; // CartPole-v1 |x| limit
const CART_W = 46;
const CART_H = 22;
const POLE_LEN = 90;

interface Props {
  observation: number[];
  width?: number;
  height?: number;
}

export default function CartPoleCanvas({ observation, width = 640, height = 260 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const [x = 0, , theta = 0] = observation;
    const groundY = 190;
    const pxPerUnit = (width - 80) / (TRACK_HALF * 2 + 0.8);
    const centreX = width / 2 + x * pxPerUnit;

    ctx.clearRect(0, 0, width, height);
    ctx.fillStyle = '#111318';
    ctx.fillRect(0, 0, width, height);

    // Track + failure-limit markers
    ctx.strokeStyle = '#2e333e';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(width / 2 - TRACK_HALF * pxPerUnit, groundY + CART_H / 2 + 6);
    ctx.lineTo(width / 2 + TRACK_HALF * pxPerUnit, groundY + CART_H / 2 + 6);
    ctx.stroke();
    ctx.strokeStyle = '#7d8593';
    ctx.setLineDash([4, 4]);
    for (const edge of [-TRACK_HALF, TRACK_HALF]) {
      const ex = width / 2 + edge * pxPerUnit;
      ctx.beginPath();
      ctx.moveTo(ex, 30);
      ctx.lineTo(ex, groundY + CART_H / 2 + 6);
      ctx.stroke();
    }
    ctx.setLineDash([]);

    // Pole (drawn first so the cart sits over its base)
    const tip = poleTip(centreX, theta, POLE_LEN);
    ctx.strokeStyle = '#e7ebf2';
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.moveTo(centreX, groundY);
    ctx.lineTo(centreX + tip.x - centreX, groundY + tip.y);
    ctx.stroke();
    // Pole tip
    ctx.fillStyle = '#bfc5ce';
    ctx.beginPath();
    ctx.arc(centreX + tip.x - centreX, groundY + tip.y, 5, 0, Math.PI * 2);
    ctx.fill();

    // Cart
    ctx.fillStyle = '#20242c';
    ctx.strokeStyle = '#bfc5ce';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.rect(centreX - CART_W / 2, groundY - CART_H / 2, CART_W, CART_H);
    ctx.fill();
    ctx.stroke();
    // Wheels
    ctx.fillStyle = '#7d8593';
    for (const wx of [-14, 14]) {
      ctx.beginPath();
      ctx.arc(centreX + wx, groundY + CART_H / 2, 5, 0, Math.PI * 2);
      ctx.fill();
    }

    // Readout
    ctx.fillStyle = '#7d8593';
    ctx.font = '12px "Roboto Mono", monospace';
    ctx.fillText(`x=${x.toFixed(3)}  theta=${theta.toFixed(3)} rad`, 12, 20);
  }, [observation, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      role="img"
      aria-label={`CartPole state: cart position ${observation[0]?.toFixed(3) ?? '—'}, pole angle ${observation[2]?.toFixed(3) ?? '—'} radians`}
      className="h-auto w-full"
      data-testid="cartpole-canvas"
    />
  );
}
