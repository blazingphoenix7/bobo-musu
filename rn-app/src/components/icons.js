import React from "react";
import Svg, { G, Path, Rect, Circle, Defs, Mask, Use, Image, Pattern } from 'react-native-svg'

export const CheckboxOnIcon = () => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='24'
		height='24'
		fill='none'
		viewBox='0 0 24 24'
	>
		<Path
			fill='#EDC77C'
			fillRule='evenodd'
			d='M5 3c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2H5zm2 9.154l1-1.077 2.571 2.77L17 7l1 1.077L10.571 16 7 12.154z'
			clipRule='evenodd'
		></Path>
	</Svg>
);

export const CheckboxOffIcon = () => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='24'
		height='24'
		fill='none'
		viewBox='0 0 24 24'
	>
		<Path
			fill='#010101'
			fillOpacity='0.5'
			fillRule='evenodd'
			d='M20 4v16H4V4h16zm-1-1H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z'
			clipRule='evenodd'
			opacity='0.54'
		></Path>
	</Svg>
);

export const CheckboxCrossIcon = () => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='24'
		height='24'
		fill='none'
		viewBox='0 0 24 24'
	>
		<Path
			fill='#FD5D31'
			fillRule='evenodd'
			d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2z'
			clipRule='evenodd'
		></Path>
		<Path
			fill='#fff'
			fillRule='evenodd'
			d='M6.882 17.118a.737.737 0 001.041 0L12 13.04l4.077 4.077a.737.737 0 001.041-1.041L13.041 12l4.077-4.077a.737.737 0 00-1.041-1.041L12 10.959 7.923 6.882a.737.737 0 00-1.04 1.041L10.958 12l-4.077 4.077a.737.737 0 000 1.04z'
			clipRule='evenodd'
		></Path>
		<Mask
			id='mask0'
			width='12'
			height='12'
			x='6'
			y='6'
			maskUnits='userSpaceOnUse'
		>
			<Path
				fill='#fff'
				fillRule='evenodd'
				d='M6.882 17.118a.737.737 0 001.041 0L12 13.04l4.077 4.077a.737.737 0 001.041-1.041L13.041 12l4.077-4.077a.737.737 0 00-1.041-1.041L12 10.959 7.923 6.882a.737.737 0 00-1.04 1.041L10.958 12l-4.077 4.077a.737.737 0 000 1.04z'
				clipRule='evenodd'
			></Path>
		</Mask>
	</Svg>
);

export const EyeIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='24'
		height='24'
		fill='none'
		viewBox='0 0 24 24'
		{...props}
	>
		<G fill='#000' fillRule='evenodd' clipRule='evenodd' opacity='0.5'>
			<Path d='M18.565 6.546a14.865 14.865 0 015.046 4.144c.519.667.519 1.6 0 2.267a14.865 14.865 0 01-5.046 4.144 14.519 14.519 0 01-6.75 1.545 14.518 14.518 0 01-6.38-1.545 14.865 14.865 0 01-5.046-4.144 1.845 1.845 0 010-2.267 14.864 14.864 0 015.046-4.144A14.52 14.52 0 0112.185 5c2.24.027 4.386.546 6.38 1.545zM1.16 12.355a13.882 13.882 0 004.712 3.87c.518.26 1.047.484 1.586.674a6.818 6.818 0 01-2.26-5.076c0-2.013.873-3.825 2.26-5.075-.539.19-1.068.415-1.586.674a13.881 13.881 0 00-4.712 3.87.865.865 0 000 1.063zM12 17.669c-3.213 0-5.827-2.622-5.827-5.846C6.173 8.6 8.787 5.978 12 5.978s5.827 2.622 5.827 5.845c0 3.224-2.614 5.846-5.827 5.846zm6.13-1.444a13.882 13.882 0 004.711-3.87.865.865 0 000-1.063 13.881 13.881 0 00-4.712-3.87 13.74 13.74 0 00-1.586-.674 6.819 6.819 0 012.26 5.075 6.819 6.819 0 01-2.258 5.074c.538-.19 1.067-.413 1.584-.672z'></Path>
			<Path d='M9.647 11.706a2.473 2.473 0 012.47-2.47 2.473 2.473 0 012.471 2.47 2.473 2.473 0 01-2.47 2.47 2.473 2.473 0 01-2.47-2.47zm.967 0c0 .829.675 1.503 1.504 1.503s1.503-.674 1.503-1.503c0-.829-.675-1.503-1.503-1.503-.83 0-1.504.674-1.504 1.503z'></Path>
		</G>
	</Svg>
);

export const BackArrowIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='18'
		height='16'
		fill='none'
		viewBox='0 0 18 16'
		{...props}
	>
		<Path
			fill='#000'
			fillRule='evenodd'
			d='M7.993 14.119c.395.432.4 1.127.007 1.558a.936.936 0 01-1.418-.004L.297 8.779a1.173 1.173 0 010-1.56L6.582.326A.94.94 0 018 .32c.39.428.392 1.121-.007 1.559L3.414 6.902h13.584C17.55 6.902 18 7.39 18 8c0 .606-.452 1.097-1.002 1.097H3.414l4.58 5.023z'
			clipRule='evenodd'
		></Path>
		<Mask
			id='mask0'
			width='19'
			height='16'
			x='0'
			y='0'
			maskUnits='userSpaceOnUse'
		>
			<Path
				fill='#fff'
				fillRule='evenodd'
				d='M7.993 14.119c.395.432.4 1.127.007 1.558a.936.936 0 01-1.418-.004L.297 8.779a1.173 1.173 0 010-1.56L6.582.326A.94.94 0 018 .32c.39.428.392 1.121-.007 1.559L3.414 6.902h13.584C17.55 6.902 18 7.39 18 8c0 .606-.452 1.097-1.002 1.097H3.414l4.58 5.023z'
				clipRule='evenodd'
			></Path>
		</Mask>
	</Svg>
);

export const MenuIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='27'
		height='18'
		fill='none'
		viewBox='0 0 27 18'
		{...props}
	>
		<Rect width='27' height='2' fill='#8E8888' rx='1'></Rect>
		<Rect width='20' height='2' y='8' fill='#8E8888' rx='1'></Rect>
		<Rect width='13' height='2' y='16' fill='#8E8888' rx='1'></Rect>
	</Svg>
);

export const HeartSolidIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='20'
		height='20'
		fill='none'
		viewBox='0 0 20 20'
	>
		<Path
			fill={props.fill || '#D09B2C'}
			fillRule='evenodd'
			d='M10.312 5.292l-.458.454-.455-.454a3.834 3.834 0 00-5.562 5.27 41.075 41.075 0 005.507 5.085c.302.23.721.23 1.023 0a40.894 40.894 0 005.508-5.084 3.834 3.834 0 00-5.563-5.271z'
			clipRule='evenodd'
		></Path>
	</Svg>
);

export const HeartHollowIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='20'
		height='20'
		fill='none'
		viewBox='0 0 20 20'
	>
		<Path
			stroke={props.stroke || '#D09B2C'}
			strokeWidth='1.5'
			d='M10.312 5.292l-.458.454-.455-.454a3.834 3.834 0 00-5.42 0v0a3.837 3.837 0 00-.142 5.27 41.074 41.074 0 005.507 5.085c.302.23.721.23 1.023 0a40.906 40.906 0 005.508-5.084 3.837 3.837 0 00-.143-5.271v0a3.834 3.834 0 00-5.42 0z'
			clipRule='evenodd'
		></Path>
	</Svg>
);

export const XIcon = props => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='15'
		height='15'
		fill='none'
		viewBox='0 0 15 15'
	>
		<Path
			fill={props.fill || '#000'}
			fillRule='evenodd'
			d='M14.697 14.697a1.036 1.036 0 01-1.464 0L7.5 8.964l-5.733 5.733a1.036 1.036 0 01-1.464-1.464L6.036 7.5.303 1.767A1.036 1.036 0 011.767.303L7.5 6.036 13.233.303a1.036 1.036 0 011.464 1.464L8.964 7.5l5.733 5.733c.404.404.404 1.06 0 1.464z'
			clipRule='evenodd'
		></Path>
	</Svg>
);

export const BackIcon = () => (
	<Svg
		xmlns='http://www.w3.org/2000/svg'
		width='18'
		height='16'
		fill='none'
		viewBox='0 0 18 16'
	>
		<Path
			fill='#000'
			fillRule='evenodd'
			d='M7.993 14.119c.395.432.4 1.127.007 1.558a.936.936 0 01-1.418-.004L.297 8.779a1.173 1.173 0 010-1.56L6.582.326A.94.94 0 018 .32c.39.428.392 1.121-.007 1.559L3.414 6.902h13.584C17.55 6.902 18 7.39 18 8c0 .606-.452 1.097-1.002 1.097H3.414l4.58 5.023z'
			clipRule='evenodd'
		></Path>
	</Svg>
);