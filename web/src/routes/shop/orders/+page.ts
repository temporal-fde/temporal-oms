import { api } from '$lib/api/client';
import { get } from 'svelte/store';
import { customerId } from '$lib/stores/customer';
import { redirect } from '@sveltejs/kit';
import type { PageLoad } from './$types';

export const load: PageLoad = async () => {
	const currentCustomerId = get(customerId);

	if (!currentCustomerId) {
		throw redirect(302, '/shop/home');
	}

	try {
		const orders = await api.getOrders(currentCustomerId);
		return { orders, customerId: currentCustomerId };
	} catch (error) {
		console.error('Failed to load orders:', error);
		return { orders: [], customerId: currentCustomerId };
	}
};
