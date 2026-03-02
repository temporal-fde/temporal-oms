import { api } from '$lib/api/client';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	try {
		const items = await api.getClothing(50);
		return { items };
	} catch (error) {
		console.error('Failed to load clothing items:', error);
		return { items: [] };
	}
};
